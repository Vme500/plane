# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
MCP Gateway — bridges user requests to official plane-mcp-server.

Read tools: execute directly via MCP.
Write tools: generate proposed_action (never execute without confirmation).

SECURITY:
- Never exposes raw MCP responses to frontend.
- Never exposes API keys, tokens, or secrets.
- Write operations require explicit user confirmation.
- All operations audited.
"""

import json
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional

from django.utils import timezone

from plane.utils.exception_logger import log_exception

from .audit_logger import create_ai_audit_event
from .mcp_config import (
    get_allowed_read_tools,
    get_mcp_api_key,
    get_mcp_args,
    get_mcp_base_url,
    get_mcp_command,
    get_mcp_workspace_slug,
    is_read_tool_allowed,
    is_write_tool_allowed,
)
from .official_mcp_client import list_tools_safe, call_tool_safe


def discover_tools() -> Dict[str, Any]:
    """
    Discover available tools from official MCP server.
    Returns safe summary, never exposes raw MCP response.
    """
    command = get_mcp_command()
    args = get_mcp_args()

    env = {
        "PLANE_API_KEY": get_mcp_api_key() or "",
        "PLANE_WORKSPACE_SLUG": get_mcp_workspace_slug(),
        "PLANE_BASE_URL": get_mcp_base_url(),
    }

    result = list_tools_safe(command=command, args=args, env=env, timeout=30.0)
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "MCP connection failed."),
            "provider": "official_plane_mcp",
        }

    tool_names = result.get("tool_names", [])
    read_tools = [t for t in tool_names if is_read_tool_allowed(t)]
    write_tools = [t for t in tool_names if is_write_tool_allowed(t)]

    return {
        "success": True,
        "provider": "official_plane_mcp",
        "tool_count": result.get("tool_count", 0),
        "read_tools": read_tools,
        "write_tools": write_tools,
        "has_create_work_item": result.get("has_create_work_item", False),
        "has_update_work_item": result.get("has_update_work_item", False),
    }


def call_read_tool(
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call a read tool via official MCP server.
    Returns sanitized result, never exposes raw MCP response.
    """
    if not is_read_tool_allowed(tool_name):
        return {"success": False, "error": "Tool not in read allowlist."}

    command = get_mcp_command()
    args = get_mcp_args()
    env = {
        "PLANE_API_KEY": get_mcp_api_key() or "",
        "PLANE_WORKSPACE_SLUG": get_mcp_workspace_slug(),
        "PLANE_BASE_URL": get_mcp_base_url(),
    }

    result = call_tool_safe(
        tool_name=tool_name,
        arguments=arguments,
        command=command,
        args=args,
        env=env,
        timeout=30.0,
    )
    return result


def _generate_confirmation_token(
    action_id: str,
    workspace_slug: str,
    actor_id: Optional[str],
    tool_name: str,
    arguments: Dict[str, Any],
) -> str:
    """Generate a signed confirmation token for write operations."""
    import json as _json
    from django.core.signing import TimestampSigner

    signer = TimestampSigner()
    payload = _json.dumps({
        "action_id": action_id,
        "workspace_slug": workspace_slug,
        "actor_id": actor_id,
        "tool_name": tool_name,
        "project_id": arguments.get("project_id"),
        "title": arguments.get("name"),
    })
    return signer.sign(payload)


def generate_write_proposal(
    tool_name: str,
    arguments: Dict[str, Any],
    workspace_slug: str,
    user,
    prompt_summary: str = "",
) -> Dict[str, Any]:
    """
    Generate a proposed_action for a write tool call.
    Never executes the write operation.

    Returns proposed_action dict for confirmation card.
    """
    import uuid as _uuid

    action_id = str(_uuid.uuid4())
    actor_id = str(user.id) if user else None

    # Build display info from arguments
    target_display = ""
    current_value = ""
    proposed_value = ""

    if tool_name == "create_work_item":
        target_display = arguments.get("name", "New work item")
        proposed_value = f"Project: {arguments.get('project_id', '?')}"
    elif tool_name == "update_work_item":
        target_display = arguments.get("work_item_id", "Work item")
        if "state_id" in arguments:
            proposed_value = f"State: {arguments['state_id']}"
        elif "priority" in arguments:
            proposed_value = f"Priority: {arguments['priority']}"

    proposed_action = {
        "action_id": action_id,
        "workspace_slug": workspace_slug,
        "actor_id": actor_id,
        "action_type": tool_name,
        "target_type": "work_item" if "work_item" in tool_name else "unknown",
        "target_id": arguments.get("work_item_id") or arguments.get("project_id"),
        "target_display": target_display,
        "current_value": current_value or None,
        "proposed_value": proposed_value or None,
        "risk_level": "medium",
        "summary": f"{tool_name}: {target_display}",
        "requires_confirmation": True,
        "expires_at": (timezone.now() + timedelta(minutes=5)).isoformat(),
        "execution_enabled": True,
        "confirmation_token": _generate_confirmation_token(action_id, workspace_slug, actor_id, tool_name, arguments),
    }

    # Audit
    create_ai_audit_event(
        event="ai.write.proposed",
        workspace_slug=workspace_slug,
        actor_id=actor_id,
        mode="mcp",
        tool_name=tool_name,
        tool_status="proposed",
        readonly=False,
        write_operation=True,
    )

    return proposed_action
