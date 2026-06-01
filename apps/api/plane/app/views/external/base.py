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
            # Phase 9.3: Handle confirm_action_id with signed token
            confirm_action_id = request.data.get("confirm_action_id")
            confirmation_token = request.data.get("confirmation_token")
            if confirm_action_id and confirmation_token:
                return self._handle_write_confirmation(
                    request, slug, user_id, confirm_action_id, confirmation_token
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

    def _handle_write_confirmation(self, request, slug, user_id, confirm_action_id, confirmation_token):
        """
        Phase 9.3: Handle confirmed write operation (update_work_item_state).

        Verifies signed token, validates permissions, and updates issue state.
        """
        import json as json_module
        from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
        from plane.db.models import Issue, State, ProjectMember, WorkspaceMember

        tool_name = "update_work_item_state"

        def _reject(error_code, message):
            create_ai_audit_event(
                event="ai.write.rejected",
                workspace_slug=slug,
                actor_id=user_id,
                mode="mcp",
                tool_name=tool_name,
                tool_status="rejected",
                readonly=False,
                write_operation=True,
                error_code=error_code,
            )
            return Response(
                {
                    "response": message,
                    "response_html": message,
                    "mode": "mcp",
                    "mcp_preview": {
                        "mode": "mcp",
                        "adapter": "none",
                        "tool": {"name": tool_name, "status": "rejected", "readonly": False},
                        "summary": message,
                        "items": [],
                        "safety": {"raw_result_returned": False, "write_operation": True, "permission_filtered": True},
                        "proposed_action": None,
                    },
                },
                status=status.HTTP_200_OK,
            )

        # Log confirmed event
        create_ai_audit_event(
            event="ai.write.confirmed",
            workspace_slug=slug,
            actor_id=user_id,
            mode="mcp",
            tool_name=tool_name,
            tool_status="confirmed",
            readonly=False,
            write_operation=True,
        )

        # Verify signed token
        signer = TimestampSigner()
        try:
            raw = signer.unsign(confirmation_token, max_age=300)
            payload = json_module.loads(raw)
        except SignatureExpired:
            return _reject("confirmation_token_expired", "Confirmation has expired. Please try again.")
        except (BadSignature, Exception):
            return _reject("confirmation_token_invalid", "Invalid confirmation token.")

        # Verify actor
        if str(payload.get("actor_id")) != str(user_id):
            return _reject("action_actor_mismatch", "Action actor mismatch.")

        # Verify workspace
        if payload.get("workspace_slug") != slug:
            return _reject("workspace_mismatch", "Workspace mismatch.")

        # Verify confirm_action_id matches token
        if str(payload.get("action_id")) != str(confirm_action_id):
            return _reject("confirmation_token_invalid", "Action ID mismatch.")

        issue_id = payload.get("issue_id")
        project_id = payload.get("project_id")
        current_state_id = payload.get("current_state_id")
        proposed_state_id = payload.get("proposed_state_id")

        if not issue_id or not proposed_state_id:
            return _reject("confirmation_token_invalid", "Invalid token payload.")

        # Verify workspace membership
        if not WorkspaceMember.objects.filter(
            workspace__slug=slug, member=request.user, is_active=True
        ).exists():
            return _reject("workspace_member_required", "Workspace membership required.")

        # Verify issue exists and belongs to workspace
        try:
            issue = Issue.objects.get(pk=issue_id, workspace__slug=slug)
        except (Issue.DoesNotExist, ValueError):
            return _reject("issue_not_found", "Work item not found.")

        # Verify issue belongs to project
        if str(issue.project_id) != str(project_id):
            return _reject("issue_workspace_mismatch", "Work item does not belong to this project.")

        # Verify project membership (ADMIN or MEMBER)
        if not ProjectMember.objects.filter(
            project_id=issue.project_id,
            member=request.user,
            role__in=[20, 15],  # ADMIN, MEMBER
            is_active=True,
        ).exists():
            return _reject("project_permission_denied", "Project permission denied.")

        # Verify current state unchanged
        current_issue_state = str(issue.state_id) if issue.state_id else None
        if current_issue_state != current_state_id:
            return _reject("current_state_mismatch", "Work item state has changed since the proposal was created.")

        # Verify proposed state belongs to same project
        try:
            proposed_state = State.objects.get(pk=proposed_state_id, project_id=issue.project_id)
        except (State.DoesNotExist, ValueError):
            return _reject("state_not_found", "Target state not found in this project.")

        # Capture old state for activity
        old_state_id = str(issue.state_id) if issue.state_id else None
        old_state_name = None
        if issue.state_id:
            try:
                old_state = State.objects.get(pk=issue.state_id)
                old_state_name = old_state.name
            except State.DoesNotExist:
                pass

        # Execute the state update
        try:
            issue.state_id = proposed_state.id
            issue.save()  # Triggers _sync_completed_at() and ChangeTrackerMixin

            # Dispatch activity task (best-effort)
            try:
                from plane.bgtasks.issue_activities_task import issue_activity
                issue_activity.delay(
                    type="issue.activity.updated",
                    requested_data=json_module.dumps({"state_id": str(proposed_state.id)}),
                    current_instance=json_module.dumps({"state_id": old_state_id}),
                    issue_id=str(issue.id),
                    actor_id=str(request.user.id),
                    project_id=str(issue.project_id),
                    workspace_slug=slug,
                )
            except Exception:
                pass  # Activity logging is best-effort

            # Log success
            create_ai_audit_event(
                event="ai.write.executed",
                workspace_slug=slug,
                actor_id=user_id,
                mode="mcp",
                tool_name=tool_name,
                tool_status="executed",
                readonly=False,
                write_operation=True,
                permission_filtered=True,
                item_count=1,
                duration_ms=duration_since(now_ms()),
            )

            summary = f"State updated: {old_state_name or '?'} → {proposed_state.name}"
            return Response(
                {
                    "response": summary,
                    "response_html": summary,
                    "mode": "mcp",
                    "mcp_preview": {
                        "mode": "mcp",
                        "adapter": "none",
                        "tool": {"name": tool_name, "status": "executed", "readonly": False},
                        "summary": summary,
                        "items": [],
                        "safety": {"raw_result_returned": False, "write_operation": True, "permission_filtered": True},
                        "proposed_action": None,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            create_ai_audit_event(
                event="ai.write.error",
                workspace_slug=slug,
                actor_id=user_id,
                mode="mcp",
                tool_name=tool_name,
                tool_status="error",
                readonly=False,
                write_operation=True,
                error_code="write_execution_failed",
            )
            return _reject("write_execution_failed", "Failed to update work item state.")


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
