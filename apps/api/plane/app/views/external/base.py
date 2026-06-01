# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python import
import os
from typing import List, Dict, Tuple

# Third party import
from openai import OpenAI
import requests

from rest_framework import status
from rest_framework.response import Response

# Module import
from plane.app.permissions import ROLE, allow_permission
from plane.app.serializers import ProjectLiteSerializer, WorkspaceLiteSerializer
from plane.db.models import Project, Workspace
from plane.license.utils.instance_value import get_configuration_value
from plane.utils.exception_logger import log_exception

from ..base import BaseAPIView

# MCP runtime imports
from plane.ai.mcp_runtime import execute_mcp_request, format_mcp_response_text, build_mcp_preview
from plane.ai.audit_logger import create_ai_audit_event, safe_error_code, now_ms, duration_since, ERROR_INVALID_MODE, ERROR_LLM_REQUEST_ERROR


class LLMProvider:
    """Base class for LLM provider configurations"""

    name: str = ""
    models: List[str] = []
    default_model: str = ""

    @classmethod
    def get_config(cls) -> Dict[str, str | List[str]]:
        return {
            "name": cls.name,
            "models": cls.models,
            "default_model": cls.default_model,
        }


class OpenAIProvider(LLMProvider):
    name = "OpenAI"
    models = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", "o1-mini", "o1-preview"]
    default_model = "gpt-4o-mini"


class AnthropicProvider(LLMProvider):
    name = "Anthropic"
    models = [
        "claude-3-5-sonnet-20240620",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-2.1",
        "claude-2",
        "claude-instant-1.2",
        "claude-instant-1",
    ]
    default_model = "claude-3-sonnet-20240229"


class GeminiProvider(LLMProvider):
    name = "Gemini"
    models = ["gemini-pro", "gemini-1.5-pro-latest", "gemini-pro-vision"]
    default_model = "gemini-pro"


SUPPORTED_PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}


def get_llm_config() -> Tuple[str | None, str | None, str | None]:
    """
    Helper to get LLM configuration values, returns:
        - api_key, model, provider
    """
    api_key, provider_key, model = get_configuration_value(
        [
            {
                "key": "LLM_API_KEY",
                "default": os.environ.get("LLM_API_KEY", None),
            },
            {
                "key": "LLM_PROVIDER",
                "default": os.environ.get("LLM_PROVIDER", "openai"),
            },
            {
                "key": "LLM_MODEL",
                "default": os.environ.get("LLM_MODEL", None),
            },
        ]
    )

    provider = SUPPORTED_PROVIDERS.get(provider_key.lower())
    if not provider:
        log_exception(ValueError(f"Unsupported provider: {provider_key}"))
        return None, None, None

    if not api_key:
        log_exception(ValueError(f"Missing API key for provider: {provider.name}"))
        return None, None, None

    # If no model specified, use provider's default
    if not model:
        model = provider.default_model

    # Validate model is supported by provider
    if model not in provider.models:
        log_exception(
            ValueError(
                f"Model {model} not supported by {provider.name}. Supported models: {', '.join(provider.models)}"
            )
        )
        return None, None, None

    return api_key, model, provider_key


def get_llm_response(task, prompt, api_key: str, model: str, provider: str) -> Tuple[str | None, str | None]:
    """Helper to get LLM completion response"""
    final_text = task + "\n" + prompt
    try:
        # For Gemini, prepend provider name to model
        if provider.lower() == "gemini":
            model = f"gemini/{model}"

        client = OpenAI(api_key=api_key)
        chat_completion = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": final_text}]
        )
        text = chat_completion.choices[0].message.content
        return text, None
    except Exception as e:
        log_exception(e)
        error_type = e.__class__.__name__
        if error_type == "AuthenticationError":
            return None, f"Invalid API key for {provider}"
        elif error_type == "RateLimitError":
            return None, f"Rate limit exceeded for {provider}"
        else:
            return None, f"Error occurred while generating response from {provider}"


class GPTIntegrationEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def post(self, request, slug, project_id):
        api_key, model, provider = get_llm_config()

        if not api_key or not model or not provider:
            return Response(
                {"error": "LLM provider API key and model are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = request.data.get("task", False)
        if not task:
            return Response({"error": "Task is required"}, status=status.HTTP_400_BAD_REQUEST)

        text, error = get_llm_response(task, request.data.get("prompt", False), api_key, model, provider)
        if not text and error:
            return Response(
                {"error": "An internal error has occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        workspace = Workspace.objects.get(slug=slug)
        project = Project.objects.get(pk=project_id)

        return Response(
            {
                "response": text,
                "response_html": text.replace("\n", "<br/>"),
                "project_detail": ProjectLiteSerializer(project).data,
                "workspace_detail": WorkspaceLiteSerializer(workspace).data,
            },
            status=status.HTTP_200_OK,
        )


class WorkspaceGPTIntegrationEndpoint(BaseAPIView):
    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        start = now_ms()
        user_id = str(request.user.id) if request.user else "unknown"
        api_key, model, provider = get_llm_config()

        if not api_key or not model or not provider:
            return Response(
                {"error": "LLM provider API key and model are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = request.data.get("task", False)
        if not task:
            return Response({"error": "Task is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if MCP mode is requested
        mode = request.data.get("mode", "standard")

        if mode == "mcp":
            # Phase 9.1: Reject any confirm_action_id (execution not enabled)
            confirm_action_id = request.data.get("confirm_action_id")
            if confirm_action_id:
                create_ai_audit_event(
                    event="ai.write.rejected",
                    workspace_slug=slug,
                    actor_id=user_id,
                    mode="mcp",
                    tool_name="update_work_item_state",
                    tool_status="rejected",
                    readonly=False,
                    write_operation=True,
                    error_code="execution_not_enabled",
                )
                return Response(
                    {
                        "response": "Write operation execution is not enabled yet. This is a plan-only preview.",
                        "response_html": "Write operation execution is not enabled yet. This is a plan-only preview.",
                        "mode": "mcp",
                        "mcp_preview": {
                            "mode": "mcp",
                            "adapter": "none",
                            "tool": {"name": "update_work_item_state", "status": "rejected", "readonly": False},
                            "summary": "Execution not enabled",
                            "items": [],
                            "safety": {"raw_result_returned": False, "write_operation": True, "permission_filtered": True},
                            "proposed_action": None,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            # MCP mode - execute read-only MCP tools
            prompt = request.data.get("prompt", "")

            create_ai_audit_event(
                event="ai.request",
                workspace_slug=slug,
                actor_id=user_id,
                mode="mcp",
                prompt_length=len(prompt) if prompt else 0,
            )

            mcp_result = execute_mcp_request(
                prompt=prompt,
                workspace_slug=slug,
                user=request.user,
            )

            # Format response
            response_text = format_mcp_response_text(mcp_result)
            response_html = response_text.replace("\n", "<br/>")

            # Build structured preview for frontend (never includes raw result)
            mcp_preview = build_mcp_preview(mcp_result)

            # Audit: log tool-level event based on mcp_preview
            tool_info = mcp_preview.get("tool", {})
            safety_info = mcp_preview.get("safety", {})
            items = mcp_preview.get("items", [])

            create_ai_audit_event(
                event="ai.tool.call" if mcp_result.get("success") else "ai.tool.error",
                workspace_slug=slug,
                actor_id=user_id,
                mode="mcp",
                adapter=mcp_preview.get("adapter", "unknown"),
                tool_name=tool_info.get("name"),
                tool_status=tool_info.get("status"),
                permission_filtered=safety_info.get("permission_filtered"),
                item_count=len(items),
                duration_ms=duration_since(start),
                error_code=safe_error_code(mcp_result.get("error")) if not mcp_result.get("success") else None,
            )

            return Response(
                {
                    "response": response_text,
                    "response_html": response_html,
                    "mode": "mcp",
                    "mcp_preview": mcp_preview,
                },
                status=status.HTTP_200_OK,
            )

        # Standard mode - original prompt-response behavior
        prompt = request.data.get("prompt", False)
        create_ai_audit_event(
            event="ai.request",
            workspace_slug=slug,
            user_id=user_id,
            mode="standard",
            prompt_length=len(prompt) if prompt else 0,
        )

        text, error = get_llm_response(task, prompt, api_key, model, provider)
        if not text and error:
            create_ai_audit_event(
                event="ai.request.error",
                workspace_slug=slug,
                actor_id=user_id,
                mode="standard",
                error_code=ERROR_LLM_REQUEST_ERROR,
                duration_ms=duration_since(start),
            )
            return Response(
                {"error": "An internal error has occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        create_ai_audit_event(
            event="ai.request.success",
            workspace_slug=slug,
            user_id=user_id,
            mode="standard",
            duration_ms=duration_since(start),
        )

        return Response(
            {
                "response": text,
                "response_html": text.replace("\n", "<br/>"),
            },
            status=status.HTTP_200_OK,
        )


class UnsplashEndpoint(BaseAPIView):
    def get(self, request):
        (UNSPLASH_ACCESS_KEY,) = get_configuration_value(
            [
                {
                    "key": "UNSPLASH_ACCESS_KEY",
                    "default": os.environ.get("UNSPLASH_ACCESS_KEY"),
                }
            ]
        )
        # Check unsplash access key
        if not UNSPLASH_ACCESS_KEY:
            return Response([], status=status.HTTP_200_OK)

        # Query parameters
        query = request.GET.get("query", False)
        page = request.GET.get("page", 1)
        per_page = request.GET.get("per_page", 20)

        url = (
            f"https://api.unsplash.com/search/photos/?client_id={UNSPLASH_ACCESS_KEY}&query={query}&page=${page}&per_page={per_page}"
            if query
            else f"https://api.unsplash.com/photos/?client_id={UNSPLASH_ACCESS_KEY}&page={page}&per_page={per_page}"
        )

        headers = {"Content-Type": "application/json"}

        resp = requests.get(url=url, headers=headers)
        return Response(resp.json(), status=resp.status_code)
