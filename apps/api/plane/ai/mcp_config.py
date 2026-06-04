# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
MCP Configuration — reads official MCP server settings from environment.

SECURITY:
- Never exposes API keys, tokens, or secrets to frontend/logs.
- Returns only safe metadata (configured=true, masked values).
"""

import os
from typing import Any, Dict, List, Optional

# Provider types
PROVIDER_OFFICIAL = "official_plane_mcp"
PROVIDER_LEGACY = "legacy_internal_pi_ai"

# Default read-only tools
DEFAULT_READ_TOOLS = [
    "get_me",
    "list_projects",
    "list_work_items",
    "list_states",
    "list_labels",
    "list_cycles",
    "list_modules",
    "retrieve_project",
    "retrieve_work_item",
    "search_work_items",
]

# Default write tools (require confirmation)
DEFAULT_WRITE_TOOLS = [
    "create_work_item",
    "update_work_item",
]

# Destructive tools (disabled by default)
DESTRUCTIVE_TOOLS = [
    "delete_work_item",
    "create_project",
    "update_project",
    "delete_project",
    "create_state",
    "update_state",
    "delete_state",
    "create_label",
    "update_label",
    "delete_label",
    "create_cycle",
    "delete_cycle",
    "create_module",
    "delete_module",
]


def get_mcp_provider() -> str:
    """Get MCP provider type. Default: official_plane_mcp."""
    return os.environ.get("PLANE_AI_MCP_PROVIDER", PROVIDER_OFFICIAL).strip().lower()


def get_mcp_command() -> str:
    """Get MCP server command. Default: uvx."""
    return os.environ.get("PLANE_AI_MCP_COMMAND", "uvx").strip()


def get_mcp_args() -> List[str]:
    """Get MCP server args. Default: plane-mcp-server stdio."""
    args_str = os.environ.get("PLANE_AI_MCP_ARGS", "plane-mcp-server stdio")
    return args_str.strip().split()


def get_mcp_base_url() -> str:
    """Get Plane API base URL for MCP server. Default: http://api:8000."""
    return os.environ.get("PLANE_AI_MCP_BASE_URL", "http://api:8000").strip()


def get_mcp_api_key() -> Optional[str]:
    """Get MCP API key. Never return to frontend."""
    return os.environ.get("PLANE_AI_MCP_API_KEY") or None


def get_mcp_workspace_slug() -> str:
    """Get workspace slug for MCP server."""
    return os.environ.get("PLANE_AI_MCP_WORKSPACE_SLUG", "").strip()


def is_write_confirmation_required() -> bool:
    """Whether write operations require confirmation. Default: True."""
    val = os.environ.get("PLANE_AI_MCP_WRITE_CONFIRMATION_REQUIRED", "true")
    return val.strip().lower() in ("true", "1", "yes")


def get_allowed_read_tools() -> List[str]:
    """Get allowed read tools list."""
    val = os.environ.get("PLANE_AI_MCP_ALLOWED_READ_TOOLS", "")
    if val.strip():
        return [t.strip() for t in val.split(",") if t.strip()]
    return DEFAULT_READ_TOOLS


def get_allowed_write_tools() -> List[str]:
    """Get allowed write tools list."""
    val = os.environ.get("PLANE_AI_MCP_ALLOWED_WRITE_TOOLS", "")
    if val.strip():
        return [t.strip() for t in val.split(",") if t.strip()]
    return DEFAULT_WRITE_TOOLS


def is_write_tool_allowed(tool_name: str) -> bool:
    """Check if a write tool is in the allowed list."""
    return tool_name in get_allowed_write_tools()


def is_read_tool_allowed(tool_name: str) -> bool:
    """Check if a read tool is in the allowed list."""
    return tool_name in get_allowed_read_tools()


def get_mcp_config_safe() -> Dict[str, Any]:
    """
    Get safe MCP config for API response.
    Never returns secrets.
    """
    api_key = get_mcp_api_key()
    return {
        "provider": get_mcp_provider(),
        "configured": bool(api_key),
        "command": get_mcp_command(),
        "base_url": get_mcp_base_url(),
        "write_confirmation_required": is_write_confirmation_required(),
        "allowed_read_tools": get_allowed_read_tools(),
        "allowed_write_tools": get_allowed_write_tools(),
        "destructive_tools": DESTRUCTIVE_TOOLS,
    }
