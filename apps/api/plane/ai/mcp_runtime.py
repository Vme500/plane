# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
MCP Runtime - Read-only MCP runtime for Plane AI Assistant.

This module provides the MCP runtime for executing read-only tools.
In Phase 6, it uses mock implementations. In future phases, it will
call the actual plane-mcp-server via subprocess or MCP SDK.
"""

import json
import os
from typing import Any, Dict, List, Optional
from plane.license.utils.instance_value import get_configuration_value
from plane.utils.exception_logger import log_exception

from .mcp_tools import READ_ONLY_TOOLS, execute_tool_mock, get_tool_description, is_tool_allowed


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


def execute_mcp_request(
    prompt: str,
    workspace_slug: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Execute an MCP request.

    This function:
    1. Checks if MCP runtime is enabled
    2. Parses the user prompt to determine tool intent
    3. Validates the tool is read-only
    4. Executes the tool (mock in Phase 6)
    5. Returns structured response

    Args:
        prompt: User's natural language prompt
        workspace_slug: Current workspace slug
        user_id: Current user ID

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

    # Execute tool
    try:
        result = execute_tool_mock(
            tool_name=tool_name,
            workspace_slug=workspace_slug,
            user_id=user_id,
            params=intent.get("params"),
        )

        # Format response for display
        if result.get("success"):
            return {
                "success": True,
                "mode": "mcp",
                "tool": tool_name,
                "tool_description": get_tool_description(tool_name),
                "result": result.get("result"),
            }
        else:
            return {
                "success": False,
                "mode": "mcp",
                "tool": tool_name,
                "error": result.get("error", "Unknown error"),
            }

    except Exception as e:
        log_exception(e)
        return {
            "success": False,
            "mode": "mcp",
            "tool": tool_name,
            "error": f"Internal error executing tool: {str(e)}",
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
