# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
MCP Tools - Read-only tool whitelist and implementations.

Follows Plane's existing API permission patterns:
- ProjectBasePermission for project list/retrieve
- ProjectEntityPermission for entity list/retrieve (issues, states, etc.)
- Workspace membership verified by endpoint decorator (defense-in-depth here too)
- Project membership checked in querysets
"""

from typing import Any, Dict, Optional
from django.db.models import Q
from plane.db.models import (
    Project,
    ProjectMember,
    State,
    Label,
    Cycle,
    Module,
    Issue,
    Workspace,
    WorkspaceMember,
)


# Read-only tool whitelist
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

# Return limits per tool
DEFAULT_LIMIT = 20
MAX_LIMIT = 50

# Safe error message - never expose internals
PERMISSION_DENIED_ERROR = "Access denied or resource not found."


def is_tool_allowed(tool_name: str) -> bool:
    """Check if a tool is in the read-only whitelist."""
    if tool_name in READ_ONLY_TOOLS:
        return True
    for pattern in PROHIBITED_PATTERNS:
        if tool_name.startswith(pattern) or f"_{pattern}" in tool_name:
            return False
    return False


def get_tool_description(tool_name: str) -> str:
    """Get description for a tool."""
    descriptions = {
        "get_me": "Get current user information",
        "list_projects": "List accessible projects in the workspace",
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


def safe_limit(requested: Optional[int], default: int = DEFAULT_LIMIT, maximum: int = MAX_LIMIT) -> int:
    """Clamp a requested limit to [1, maximum]."""
    if requested is None:
        return default
    try:
        v = int(requested)
    except (TypeError, ValueError):
        return default
    return max(1, min(v, maximum))


def _require_workspace_member(user, workspace_slug: str) -> Optional[Workspace]:
    """
    Return workspace if user is an active member, else None.
    Defense-in-depth: endpoint decorator already enforces this.
    """
    try:
        wm = WorkspaceMember.objects.select_related("workspace").get(
            workspace__slug=workspace_slug,
            member=user,
            is_active=True,
        )
        return wm.workspace
    except WorkspaceMember.DoesNotExist:
        return None


def _get_accessible_projects_qs(user, workspace_slug: str):
    """
    Return queryset of projects accessible to user in workspace.
    Mirrors ProjectListCreateAPIEndpoint.get_queryset():
      - workspace slug filter
      - membership OR public network
      - SoftDeletionManager handles deleted_at automatically
    """
    return Project.objects.filter(
        workspace__slug=workspace_slug,
    ).filter(
        Q(project_projectmember__member=user, project_projectmember__is_active=True)
        | Q(network=2)
    )


def _get_accessible_project_or_none(user, workspace_slug: str, project_id: str) -> Optional[Project]:
    """
    Return project if it belongs to workspace AND user can access it.
    Mirrors ProjectBasePermission + queryset filtering.
    Returns None on any failure (fail-closed, no existence leak).
    """
    try:
        return _get_accessible_projects_qs(user, workspace_slug).get(pk=project_id)
    except (Project.DoesNotExist, ValueError):
        return None


def _get_project_or_none(user, workspace_slug: str, project_id: str) -> Optional[Project]:
    """
    Return project if user is an active project member.
    For entity-level tools that require ProjectEntityPermission.
    Mirrors the membership check in state/label/cycle/module/issue list APIs.
    """
    try:
        return Project.objects.filter(
            workspace__slug=workspace_slug,
            pk=project_id,
            project_projectmember__member=user,
            project_projectmember__is_active=True,
        ).get()
    except (Project.DoesNotExist, ValueError):
        return None


def execute_tool_mock(
    tool_name: str,
    workspace_slug: str,
    user,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute read-only MCP tools with proper permission checks.

    Permission model (mirrors Plane API):
    - Workspace membership verified by endpoint + defense-in-depth here
    - Project list: membership OR public network (ProjectBasePermission)
    - Project retrieve: same as list (ProjectBasePermission)
    - Entity tools (issues, states, etc.): project membership required (ProjectEntityPermission)
    - All queries filter archived entities per Plane's existing patterns
    - SoftDeletionManager handles deleted_at automatically

    Args:
        tool_name: Name of the tool to execute
        workspace_slug: Current workspace slug
        user: Django User object (request.user)
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

    params = params or {}

    # === get_me ===
    if tool_name == "get_me":
        return {
            "success": True,
            "tool": tool_name,
            "result": {
                "user_id": str(user.id),
            },
        }

    # === list_projects ===
    elif tool_name == "list_projects":
        try:
            workspace = _require_workspace_member(user, workspace_slug)
            if not workspace:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            limit = safe_limit(params.get("limit"))
            projects = _get_accessible_projects_qs(user, workspace_slug).values(
                "id", "name", "identifier", "description"
            )[:limit]
            project_list = list(projects)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "projects": project_list,
                    "count": len(project_list),
                },
            }
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === retrieve_project ===
    elif tool_name == "retrieve_project":
        project_id = params.get("project_id")
        if not project_id:
            return {"success": False, "tool": tool_name, "error": "project_id is required"}
        try:
            project = _get_accessible_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}
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
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === list_work_items ===
    elif tool_name == "list_work_items":
        project_id = params.get("project_id")
        if not project_id:
            return {"success": False, "tool": tool_name, "error": "project_id is required"}
        try:
            project = _get_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            limit = safe_limit(params.get("limit"))
            # Use Issue.issue_objects for automatic filtering:
            # - excludes soft-deleted (SoftDeletionManager)
            # - excludes archived issues
            # - excludes archived project issues
            # - excludes triage state
            # - excludes drafts
            issues = Issue.issue_objects.filter(
                project_id=project.id,
                workspace__slug=workspace_slug,
            ).values("id", "name", "state__name", "priority")[:limit]
            issue_list = list(issues)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "work_items": issue_list,
                    "count": len(issue_list),
                },
            }
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === search_work_items ===
    elif tool_name == "search_work_items":
        query = str(params.get("query", "")).strip()[:200]  # Length limit
        project_id = params.get("project_id")
        if not project_id:
            return {"success": False, "tool": tool_name, "error": "project_id is required"}
        if not query:
            return {"success": False, "tool": tool_name, "error": "query is required"}
        try:
            project = _get_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            limit = safe_limit(params.get("limit"), default=20, maximum=20)
            issues = Issue.issue_objects.filter(
                project_id=project.id,
                workspace__slug=workspace_slug,
                name__icontains=query,
            ).values("id", "name", "state__name", "priority")[:limit]
            issue_list = list(issues)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "work_items": issue_list,
                    "count": len(issue_list),
                    "query": query,
                },
            }
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === retrieve_work_item ===
    elif tool_name == "retrieve_work_item":
        work_item_id = params.get("work_item_id")
        if not work_item_id:
            return {"success": False, "tool": tool_name, "error": "work_item_id is required"}
        try:
            # Use issue_objects for automatic filtering
            issue = Issue.issue_objects.filter(
                pk=work_item_id,
                workspace__slug=workspace_slug,
            ).select_related("project").first()
            if not issue:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            # Verify user is member of the issue's project
            is_member = ProjectMember.objects.filter(
                project_id=issue.project_id,
                member=user,
                is_active=True,
            ).exists()
            if not is_member:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

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
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === list_states ===
    elif tool_name == "list_states":
        project_id = params.get("project_id")
        if not project_id:
            return {"success": False, "tool": tool_name, "error": "project_id is required"}
        try:
            project = _get_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            limit = safe_limit(params.get("limit"))
            # Mirrors state list API: workspace + project + membership + no triage + no archived project
            states = State.objects.filter(
                workspace__slug=workspace_slug,
                project_id=project.id,
                project__project_projectmember__member=user,
                project__project_projectmember__is_active=True,
                is_triage=False,
                project__archived_at__isnull=True,
            ).values("id", "name", "group", "color")[:limit]
            state_list = list(states)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "states": state_list,
                    "count": len(state_list),
                },
            }
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === list_labels ===
    elif tool_name == "list_labels":
        project_id = params.get("project_id")
        if not project_id:
            return {"success": False, "tool": tool_name, "error": "project_id is required"}
        try:
            project = _get_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            limit = safe_limit(params.get("limit"))
            # Mirrors label list API: workspace + project + membership + no archived project
            labels = Label.objects.filter(
                workspace__slug=workspace_slug,
                project_id=project.id,
                project__project_projectmember__member=user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            ).values("id", "name", "color")[:limit]
            label_list = list(labels)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "labels": label_list,
                    "count": len(label_list),
                },
            }
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === list_cycles ===
    elif tool_name == "list_cycles":
        project_id = params.get("project_id")
        if not project_id:
            return {"success": False, "tool": tool_name, "error": "project_id is required"}
        try:
            project = _get_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            limit = safe_limit(params.get("limit"))
            # Mirrors cycle list API: workspace + project + membership + exclude archived cycles
            cycles = Cycle.objects.filter(
                workspace__slug=workspace_slug,
                project_id=project.id,
                project__project_projectmember__member=user,
                project__project_projectmember__is_active=True,
                archived_at__isnull=True,
            ).values("id", "name", "start_date", "end_date")[:limit]
            cycle_list = list(cycles)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "cycles": cycle_list,
                    "count": len(cycle_list),
                },
            }
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    # === list_modules ===
    elif tool_name == "list_modules":
        project_id = params.get("project_id")
        if not project_id:
            return {"success": False, "tool": tool_name, "error": "project_id is required"}
        try:
            project = _get_project_or_none(user, workspace_slug, str(project_id))
            if not project:
                return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

            limit = safe_limit(params.get("limit"))
            # Mirrors module list API: workspace + project + membership + exclude archived modules
            modules = Module.objects.filter(
                workspace__slug=workspace_slug,
                project_id=project.id,
                project__project_projectmember__member=user,
                project__project_projectmember__is_active=True,
                archived_at__isnull=True,
            ).values("id", "name", "description", "start_date", "target_date")[:limit]
            module_list = list(modules)
            return {
                "success": True,
                "tool": tool_name,
                "result": {
                    "modules": module_list,
                    "count": len(module_list),
                },
            }
        except Exception:
            return {"success": False, "tool": tool_name, "error": PERMISSION_DENIED_ERROR}

    return {
        "success": False,
        "tool": tool_name,
        "error": f"Tool '{tool_name}' is not implemented",
    }
