# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
MCP Tools - Read-only tool whitelist and mock implementations.

This module defines the allowed read-only MCP tools for Phase 6.
Write operations (create, update, delete, etc.) are explicitly prohibited.
"""

from typing import Any, Dict, List, Optional
from plane.db.models import Project, State, Label, Cycle, Module, Issue
from plane.db.models import Workspace


# Read-only tool whitelist
# Only these tools are allowed in MCP read-only mode
READ_ONLY_TOOLS = [
    "get_me",
    "list_projects",
    "retrieve_project",
    "list_work_items",
    "search_work_items",
    "retrieve_work_item",
    "list_states",
    "list_labels",
    "list_cycles",
    "list_modules",
]

# Prohibited tool patterns - any tool matching these patterns is blocked
PROHIBITED_PATTERNS = [
    "create",
    "update",
    "delete",
    "assign",
    "move",
    "archive",
    "bulk",
    "import",
    "upload",
    "set_",
    "add_",
    "remove_",
    "patch",
    "put",
]


def is_tool_allowed(tool_name: str) -> bool:
    """Check if a tool is in the read-only whitelist."""
    if tool_name in READ_ONLY_TOOLS:
        return True
    # Check for prohibited patterns
    for pattern in PROHIBITED_PATTERNS:
        if tool_name.startswith(pattern) or f"_{pattern}" in tool_name:
            return False
    return False


def get_tool_description(tool_name: str) -> str:
    """Get description for a tool."""
    descriptions = {
        "get_me": "Get current user information",
        "list_projects": "List all projects in the workspace",
        "retrieve_project": "Get details of a specific project",
        "list_work_items": "List work items in a project",
        "search_work_items": "Search work items by query",
        "retrieve_work_item": "Get details of a specific work item",
        "list_states": "List states in a project",
        "list_labels": "List labels in a project",
        "list_cycles": "List cycles in a project",
        "list_modules": "List modules in a project",
    }
    return descriptions.get(tool_name, "Unknown tool")


def execute_tool_mock(
    tool_name: str,
    workspace_slug: str,
    user_id: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Mock execution of MCP tools.

    In Phase 6, this returns mock data for testing.
    In production, this would call the actual plane-mcp-server.

    Args:
        tool_name: Name of the tool to execute
        workspace_slug: Current workspace slug
        user_id: Current user ID
        params: Optional parameters for the tool

    Returns:
        Dict with tool execution results
    """
    if not is_tool_allowed(tool_name):
        return {
            "success": False,
            "error": f"Tool '{tool_name}' is not allowed in read-only mode",
            "tool": tool_name,
        }

    # Mock implementations for read-only tools
    if tool_name == "get_me":
        return {
            "success": True,
            "tool": tool_name,
            "result": {
                "user_id": user_id,
                "message": "User information retrieved successfully",
            },
        }

    elif tool_name == "list_projects":
        try:
            workspace = Workspace.objects.get(slug=workspace_slug)
            projects = Project.objects.filter(workspace=workspace).values(
                "id", "name", "identifier", "description"
            )
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "projects": list(projects),
                    "count": len(projects),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Failed to list projects: {str(e)}",
            }

    elif tool_name == "retrieve_project":
        project_id = params.get("project_id") if params else None
        if not project_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "project_id is required",
            }
        try:
            project = Project.objects.get(pk=project_id)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "id": str(project.id),
                    "name": project.name,
                    "identifier": project.identifier,
                    "description": project.description,
                },
            }
        except Project.DoesNotExist:
            return {
                "success": False,
                "tool": tool_name,
                "error": "Project not found",
            }

    elif tool_name == "list_work_items":
        project_id = params.get("project_id") if params else None
        if not project_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "project_id is required",
            }
        try:
            issues = Issue.objects.filter(project_id=project_id).values(
                "id", "name", "state__name", "priority"
            )[:50]  # Limit to 50 items
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "work_items": list(issues),
                    "count": len(issues),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Failed to list work items: {str(e)}",
            }

    elif tool_name == "search_work_items":
        query = params.get("query", "") if params else ""
        project_id = params.get("project_id") if params else None
        if not project_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "project_id is required",
            }
        try:
            issues = Issue.objects.filter(
                project_id=project_id, name__icontains=query
            ).values("id", "name", "state__name", "priority")[:20]
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "work_items": list(issues),
                    "count": len(issues),
                    "query": query,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Failed to search work items: {str(e)}",
            }

    elif tool_name == "retrieve_work_item":
        work_item_id = params.get("work_item_id") if params else None
        if not work_item_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "work_item_id is required",
            }
        try:
            issue = Issue.objects.get(pk=work_item_id)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "id": str(issue.id),
                    "name": issue.name,
                    "description": issue.description,
                    "state": issue.state.name if issue.state else None,
                    "priority": issue.priority,
                },
            }
        except Issue.DoesNotExist:
            return {
                "success": False,
                "tool": tool_name,
                "error": "Work item not found",
            }

    elif tool_name == "list_states":
        project_id = params.get("project_id") if params else None
        if not project_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "project_id is required",
            }
        try:
            states = State.objects.filter(project_id=project_id).values(
                "id", "name", "group", "color"
            )
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "states": list(states),
                    "count": len(states),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Failed to list states: {str(e)}",
            }

    elif tool_name == "list_labels":
        project_id = params.get("project_id") if params else None
        if not project_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "project_id is required",
            }
        try:
            labels = Label.objects.filter(project_id=project_id).values(
                "id", "name", "color"
            )
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "labels": list(labels),
                    "count": len(labels),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Failed to list labels: {str(e)}",
            }

    elif tool_name == "list_cycles":
        project_id = params.get("project_id") if params else None
        if not project_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "project_id is required",
            }
        try:
            cycles = Cycle.objects.filter(project_id=project_id).values(
                "id", "name", "start_date", "end_date"
            )
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "cycles": list(cycles),
                    "count": len(cycles),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Failed to list cycles: {str(e)}",
            }

    elif tool_name == "list_modules":
        project_id = params.get("project_id") if params else None
        if not project_id:
            return {
                "success": False,
                "tool": tool_name,
                "error": "project_id is required",
            }
        try:
            modules = Module.objects.filter(project_id=project_id).values(
                "id", "name", "description", "start_date", "target_date"
            )
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "modules": list(modules),
                    "count": len(modules),
                },
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"Failed to list modules: {str(e)}",
            }

    return {
        "success": False,
        "tool": tool_name,
        "error": f"Tool '{tool_name}' is not implemented",
    }
