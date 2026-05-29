# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
MCP Runtime - Read-only MCP runtime for Plane AI Assistant.

Dispatches to one of two adapters based on AI_MCP_ADAPTER:
  - mock:  Direct DB query (Phase 6, default). Per-user permissions enforced.
  - stdio: Real plane-mcp-server via subprocess (Phase 6.8/6.9).
           Uses workspace API key — NOT per-user.
           Safety gate: only get_me, list_projects (filtered), retrieve_project
           (validated) are allowed through. All other tools blocked until
           per-user permission filtering is implemented.

No automatic fallback: if stdio fails, returns an error (avoids misleading
the user into thinking data came from the MCP server when it came from mock).
"""

import json
import os
from typing import Any, Dict, List, Optional
from plane.license.utils.instance_value import get_configuration_value
from plane.utils.exception_logger import log_exception

from .mcp_tools import (
    READ_ONLY_TOOLS,
    execute_tool_mock,
    get_tool_description,
    is_tool_allowed,
    _get_accessible_projects_qs,
    _get_accessible_project_or_none,
    PERMISSION_DENIED_ERROR,
)

# --- Stdio safety gate (Phase 6.9) ---
# Tools that pass through stdio without workspace/project data: safe.
_STDIO_PASS_THROUGH = {"get_me"}

# Tools that can be post-filtered against user's accessible projects.
_STDIO_FILTERABLE = {"list_projects", "retrieve_project"}

# Blocked until per-user permission filtering is implemented.
_STDIO_BLOCKED_MSG = (
    "This tool is not available via MCP stdio adapter until per-user "
    "permission filtering is implemented. Use standard chat mode instead."
)


def is_mcp_runtime_enabled() -> bool:
    """Check if MCP runtime is enabled via environment variable."""
    try:
        (enable_mcp_runtime,) = get_configuration_value(
            [
                {
                    "key": "ENABLE_AI_MCP_RUNTIME",
                    "default": os.environ.get("ENABLE_AI_MCP_RUNTIME", "0"),
                }
            ]
        )
        return str(enable_mcp_runtime).lower() in ("1", "true")
    except Exception as e:
        log_exception(e)
        return False


def parse_mcp_intent(prompt: str) -> Dict[str, Any]:
    """
    Parse user prompt to determine which MCP tool to call.

    This is a simple keyword-based parser for Phase 6.
    In production, this would use LLM function calling or a more
    sophisticated intent detection system.

    Args:
        prompt: User's natural language prompt

    Returns:
        Dict with tool_name and params
    """
    prompt_lower = prompt.lower().strip()

    # Simple keyword matching for read-only tools
    if any(word in prompt_lower for word in ["who am i", "my info", "my profile", "about me"]):
        return {"tool_name": "get_me", "params": {}}

    if any(word in prompt_lower for word in ["list projects", "show projects", "all projects", "my projects"]):
        return {"tool_name": "list_projects", "params": {}}

    if any(word in prompt_lower for word in ["list states", "show states", "all states"]):
        # Need project_id - will be extracted from context
        return {"tool_name": "list_states", "params": {}}

    if any(word in prompt_lower for word in ["list labels", "show labels", "all labels"]):
        return {"tool_name": "list_labels", "params": {}}

    if any(word in prompt_lower for word in ["list cycles", "show cycles", "all cycles"]):
        return {"tool_name": "list_cycles", "params": {}}

    if any(word in prompt_lower for word in ["list modules", "show modules", "all modules"]):
        return {"tool_name": "list_modules", "params": {}}

    if any(word in prompt_lower for word in ["list work items", "list issues", "show issues", "all issues"]):
        return {"tool_name": "list_work_items", "params": {}}

    if any(word in prompt_lower for word in ["search", "find"]):
        return {"tool_name": "search_work_items", "params": {"query": prompt}}

    # Default: not recognized as an MCP tool request
    return {"tool_name": None, "params": {}}


def _get_adapter_type() -> str:
    """Read AI_MCP_ADAPTER from env. Default: 'mock'."""
    return os.environ.get("AI_MCP_ADAPTER", "mock").strip().lower()


def _filter_stdio_result(
    user,
    workspace_slug: str,
    tool_name: str,
    raw_result: Any,
    arguments: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Post-filter stdio MCP results against the current user's permissions.

    Phase 6.9 safety gate:
    - get_me: pass through (no workspace/project data)
    - list_projects: filter to user's accessible projects
    - retrieve_project: validate user has access to the specific project
    - All other tools: blocked (return error)

    Returns:
        {"success": True, "result": filtered_data} or
        {"success": False, "error": safe_error_message}
    """
    # --- get_me: safe to pass through ---
    if tool_name == "get_me":
        return {"success": True, "result": raw_result}

    # --- list_projects: filter to accessible projects ---
    if tool_name == "list_projects":
        try:
            # raw_result should be a list of project objects from MCP server
            if not isinstance(raw_result, list):
                return {"success": False, "error": PERMISSION_DENIED_ERROR}

            # Get user's accessible project IDs
            accessible_ids = set(
                _get_accessible_projects_qs(user, workspace_slug).values_list("id", flat=True)
            )

            # Filter MCP results to only include accessible projects
            filtered = []
            for proj in raw_result:
                if not isinstance(proj, dict):
                    continue
                proj_id = proj.get("id")
                if proj_id and _uuid_eq(proj_id, accessible_ids):
                    filtered.append({
                        "id": proj.get("id"),
                        "name": proj.get("name"),
                        "identifier": proj.get("identifier"),
                        "description": proj.get("description"),
                    })

            return {"success": True, "result": {"projects": filtered, "count": len(filtered)}}
        except Exception:
            return {"success": False, "error": PERMISSION_DENIED_ERROR}

    # --- retrieve_project: validate access ---
    if tool_name == "retrieve_project":
        try:
            # Get project_id from arguments or from MCP result
            project_id = (arguments or {}).get("project_id")
            if not project_id and isinstance(raw_result, dict):
                project_id = raw_result.get("id")
            if not project_id:
                return {"success": False, "error": PERMISSION_DENIED_ERROR}

            project = _get_accessible_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "error": PERMISSION_DENIED_ERROR}

            # Return only safe fields from validated project
            return {
                "success": True,
                "result": {
                    "id": str(project.id),
                    "name": project.name,
                    "identifier": project.identifier,
                    "description": project.description,
                },
            }
        except Exception:
            return {"success": False, "error": PERMISSION_DENIED_ERROR}

    # --- All other tools: blocked in stdio mode ---
    return {"success": False, "error": _STDIO_BLOCKED_MSG}


def _uuid_eq(value, id_set) -> bool:
    """Check if a string UUID value matches any ID in a set."""
    try:
        from uuid import UUID
        val_uuid = UUID(str(value))
        return val_uuid in id_set
    except (ValueError, TypeError, AttributeError):
        return False


def execute_mcp_request(
    prompt: str,
    workspace_slug: str,
    user,
) -> Dict[str, Any]:
    """
    Execute an MCP request.

    Dispatches to mock (direct DB) or stdio (real plane-mcp-server) adapter
    based on AI_MCP_ADAPTER env var.

    Args:
        prompt: User's natural language prompt
        workspace_slug: Current workspace slug
        user: Django User object (request.user)

    Returns:
        Dict with response data
    """
    # Check if MCP runtime is enabled
    if not is_mcp_runtime_enabled():
        return {
            "success": False,
            "error": "MCP runtime is not enabled. Set ENABLE_AI_MCP_RUNTIME=1 to enable.",
            "mode": "mcp",
        }

    # Parse intent
    intent = parse_mcp_intent(prompt)
    tool_name = intent.get("tool_name")

    if not tool_name:
        return {
            "success": False,
            "error": "Could not determine which MCP tool to call. Try asking about projects, work items, states, labels, cycles, or modules.",
            "mode": "mcp",
            "available_tools": [get_tool_description(t) for t in READ_ONLY_TOOLS],
        }

    # Validate tool is allowed
    if not is_tool_allowed(tool_name):
        return {
            "success": False,
            "error": f"Tool '{tool_name}' is not allowed in read-only mode.",
            "mode": "mcp",
        }

    adapter = _get_adapter_type()

    # --- Mock adapter (Phase 6, default) ---
    if adapter == "mock":
        try:
            result = execute_tool_mock(
                tool_name=tool_name,
                workspace_slug=workspace_slug,
                user=user,
                params=intent.get("params"),
            )
            if result.get("success"):
                return {
                    "success": True,
                    "mode": "mcp",
                    "adapter": "mock",
                    "tool": tool_name,
                    "tool_description": get_tool_description(tool_name),
                    "result": result.get("result"),
                }
            else:
                return {
                    "success": False,
                    "mode": "mcp",
                    "adapter": "mock",
                    "tool": tool_name,
                    "error": result.get("error", "Unknown error"),
                }
        except Exception as e:
            log_exception(e)
            return {
                "success": False,
                "mode": "mcp",
                "adapter": "mock",
                "tool": tool_name,
                "error": "Internal error executing tool.",
            }

    # --- Stdio adapter (Phase 6.8/6.9, real plane-mcp-server) ---
    elif adapter == "stdio":
        # Safety gate: only allow tools that can be post-filtered or are safe
        if tool_name not in _STDIO_PASS_THROUGH and tool_name not in _STDIO_FILTERABLE:
            return {
                "success": False,
                "mode": "mcp",
                "adapter": "stdio",
                "tool": tool_name,
                "error": _STDIO_BLOCKED_MSG,
            }

        try:
            from .mcp_stdio_adapter import call_tool_stdio

            result = call_tool_stdio(
                tool_name=tool_name,
                arguments=intent.get("params"),
            )
            if not result.get("success"):
                return {
                    "success": False,
                    "mode": "mcp",
                    "adapter": "stdio",
                    "tool": tool_name,
                    "error": result.get("error", "Unknown error"),
                }

            # Post-filter against user permissions
            raw_data = result.get("result")
            filtered = _filter_stdio_result(
                user=user,
                workspace_slug=workspace_slug,
                tool_name=tool_name,
                raw_result=raw_data,
                arguments=intent.get("params"),
            )

            if filtered.get("success"):
                return {
                    "success": True,
                    "mode": "mcp",
                    "adapter": "stdio",
                    "tool": tool_name,
                    "tool_description": get_tool_description(tool_name),
                    "result": filtered.get("result"),
                }
            else:
                return {
                    "success": False,
                    "mode": "mcp",
                    "adapter": "stdio",
                    "tool": tool_name,
                    "error": filtered.get("error", PERMISSION_DENIED_ERROR),
                }

        except Exception as e:
            log_exception(e)
            return {
                "success": False,
                "mode": "mcp",
                "adapter": "stdio",
                "tool": tool_name,
                "error": "MCP stdio adapter error.",
            }

    # --- Unknown adapter ---
    else:
        return {
            "success": False,
            "mode": "mcp",
            "error": f"Unsupported AI_MCP_ADAPTER value: '{adapter}'. Use 'mock' or 'stdio'.",
        }


def format_mcp_response_text(mcp_result: Dict[str, Any]) -> str:
    """
    Format MCP result as human-readable text.

    Args:
        mcp_result: Result from execute_mcp_request

    Returns:
        Formatted text string
    """
    if not mcp_result.get("success"):
        return f"Error: {mcp_result.get('error', 'Unknown error')}"

    tool = mcp_result.get("tool", "")
    result = mcp_result.get("result", {})
    description = mcp_result.get("tool_description", "")

    if tool == "get_me":
        return f"User ID: {result.get('user_id')}"

    elif tool in ["list_projects", "list_work_items", "search_work_items",
                   "list_states", "list_labels", "list_cycles", "list_modules"]:
        items = result.get("projects") or result.get("work_items") or \
                result.get("states") or result.get("labels") or \
                result.get("cycles") or result.get("modules") or []
        count = result.get("count", 0)

        if count == 0:
            return f"No {description.lower().replace('list ', '').replace('get ', '')} found."

        lines = [f"Found {count} item(s):"]
        for item in items[:10]:  # Limit to 10 items in display
            name = item.get("name") or item.get("identifier") or str(item.get("id", ""))
            lines.append(f"- {name}")

        if count > 10:
            lines.append(f"... and {count - 10} more")

        return "\n".join(lines)

    elif tool == "retrieve_project" or tool == "retrieve_work_item":
        name = result.get("name", "")
        desc = result.get("description", "")
        return f"{name}\n{desc}" if desc else name

    return json.dumps(result, indent=2, default=str)
