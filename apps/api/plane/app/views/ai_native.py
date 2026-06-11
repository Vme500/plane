# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Native AI Endpoint — official MCP gateway only.

SECURITY:
- Never imports mcp_runtime legacy module.
- Never uses legacy pi-ai parser.
- Never uses direct DB adapter as primary path.
- Only routes through official_mcp_gateway.
- Never returns confirmation_token to frontend.
- Never returns raw MCP result.
"""

import json
import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.ai.audit_logger import create_ai_audit_event
from plane.ai.mcp_config import get_mcp_config_safe, is_write_tool_allowed
from plane.ai.mcp_gateway import discover_tools, generate_write_proposal

from .base import BaseAPIView


class NativeAIStatusEndpoint(BaseAPIView):
    """GET /api/workspaces/<slug>/ai-assistant/native/status/"""

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        config = get_mcp_config_safe()
        tools = discover_tools()
        return Response(
            {
                "route": "official_mcp",
                "source": "official_mcp_gateway",
                "provider": config.get("provider"),
                "configured": config.get("configured"),
                "tool_count": tools.get("tool_count", 0),
                "has_create_work_item": tools.get("has_create_work_item", False),
                "has_update_work_item": tools.get("has_update_work_item", False),
                "write_confirmation_required": config.get("write_confirmation_required", True),
                "allowed_write_tools": config.get("allowed_write_tools", []),
            },
            status=status.HTTP_200_OK,
        )


class NativeAIProposeEndpoint(BaseAPIView):
    """POST /api/workspaces/<slug>/ai-assistant/native/propose/

    Only routes through official MCP gateway.
    Never imports mcp_runtime. Never uses legacy parser.
    """

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        message = request.data.get("message", "").strip()
        context = request.data.get("context", {})
        project_id = context.get("project_id")
        project_name = context.get("project_name", "")

        if not message:
            return Response(
                {"route": "official_mcp", "source": "official_mcp_gateway", "error": "Message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse intent — deterministic dev fallback within official MCP gateway
        tool_name, parsed = _parse_intent(message)

        if not tool_name:
            return Response(
                {
                    "route": "official_mcp",
                    "source": "official_mcp_gateway",
                    "response_type": "text",
                    "message": "Could not determine an action. Try: 'create a work item named X' or 'change state of Y to Z'.",
                },
                status=status.HTTP_200_OK,
            )

        # Verify tool exists in official MCP
        tools_result = discover_tools()
        available = tools_result.get("read_tools", []) + tools_result.get("write_tools", [])
        if tool_name not in available:
            return Response(
                {
                    "route": "official_mcp",
                    "source": "official_mcp_gateway",
                    "response_type": "error",
                    "error": f"Tool '{tool_name}' is not available in official MCP.",
                },
                status=status.HTTP_200_OK,
            )

        # For write tools, generate proposed_action
        if is_write_tool_allowed(tool_name):
            # Resolve project if not provided
            if not project_id and not project_name:
                # Try to find default project from message context
                from plane.db.models import Project
                from plane.ai.mcp_config import get_mcp_workspace_slug
                ws_slug = get_mcp_workspace_slug() or slug
                proj = Project.objects.filter(
                    workspace__slug=ws_slug,
                    project_projectmember__member=request.user,
                    project_projectmember__is_active=True,
                ).first()
                if proj:
                    project_id = str(proj.id)
                    project_name = proj.name

            arguments = {}
            if project_id:
                arguments["project_id"] = project_id
            if parsed.get("title"):
                arguments["name"] = parsed["title"]

            proposal = generate_write_proposal(
                tool_name=tool_name,
                arguments=arguments,
                workspace_slug=slug,
                user=request.user,
                prompt_summary=message,
            )

            # Build project info for response — always resolve
            project_info = None
            if project_id and project_name:
                project_info = {"id": project_id, "name": project_name}
            elif proposal.get("project"):
                project_info = proposal["project"]
            # Fallback: resolve from project_id in arguments
            if not project_info and arguments.get("project_id"):
                from plane.db.models import Project as _Proj
                _p = _Proj.objects.filter(id=arguments["project_id"]).first()
                if _p:
                    project_info = {"id": str(_p.id), "name": _p.name}
            # Fallback: first project in workspace
            if not project_info:
                from plane.db.models import Project as _Proj
                _ws = get_mcp_workspace_slug() or slug
                _p = _Proj.objects.filter(workspace__slug=_ws).first()
                if _p:
                    project_info = {"id": str(_p.id), "name": _p.name}

            return Response(
                {
                    "route": "official_mcp",
                    "source": "official_mcp_gateway",
                    "response_type": "proposed_action",
                    "raw_result_returned": False,
                    "proposed_action": {
                        "source": "official_mcp_gateway",
                        "action_id": proposal.get("action_id"),
                        "action_type": tool_name,
                        "target_type": proposal.get("target_type", "work_item"),
                        "target_display": proposal.get("target_display", parsed.get("title", "")),
                        "title": parsed.get("title", ""),
                        "project": project_info,
                        "risk_level": proposal.get("risk_level", "medium"),
                        "requires_confirmation": proposal.get("requires_confirmation", True),
                        "execution_enabled": proposal.get("execution_enabled", True),
                        "confirmation_token_present": bool(proposal.get("confirmation_token")),
                        "expires_at": proposal.get("expires_at"),
                        "summary": proposal.get("summary", ""),
                    },
                },
                status=status.HTTP_200_OK,
            )

        # For read tools, execute directly (future)
        return Response(
            {
                "route": "official_mcp",
                "source": "official_mcp_gateway",
                "response_type": "text",
                "message": f"Read tool '{tool_name}' execution not yet implemented in native endpoint.",
            },
            status=status.HTTP_200_OK,
        )


def _parse_intent(message: str):
    """
    Deterministic dev-only intent parser for MVP.
    Located inside the native endpoint, NOT in mcp_runtime.
    Will be replaced by LLM tool-calling.

    Returns: (tool_name, parsed_params) or (None, {})
    """
    import re

    msg = message.lower().strip()

    # create_work_item
    if any(w in msg for w in ["新增", "创建", "新建", "create work item", "create issue", "add a work item"]):
        title = None
        title_match = re.search(r'(?:命名为|名为|title[:\s]*)["“]?([^"”]+)["”]?', message)
        if title_match:
            title = title_match.group(1).strip()
        if not title:
            # Try to extract after "一个" or "an"
            fallback = re.search(r'(?:一个|an?)\s+(?:work item|issue)?\s*,?\s*(?:命名为|名为|called|named)\s*["“]?([^"”]+)', message)
            if fallback:
                title = fallback.group(1).strip()
        return "create_work_item", {"title": title or "New work item"}

    # update_work_item_state
    if any(w in msg for w in ["change state", "update status", "mark as", "set state", "move to", "状态改为", "状态更改为", "改为", "状态设为"]):
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        uuids = re.findall(uuid_pattern, msg)
        params = {}
        if len(uuids) >= 1:
            params["issue_id"] = uuids[0]
        if len(uuids) >= 2:
            params["proposed_state_id"] = uuids[1]
        return "update_work_item_state", params

    return None, {}
