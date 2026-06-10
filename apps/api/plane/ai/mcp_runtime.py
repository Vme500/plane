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
from .audit_logger import (
    create_ai_audit_event,
    safe_error_code,
    ERROR_MCP_RUNTIME_DISABLED,
    ERROR_TOOL_NOT_ALLOWED,
    ERROR_STDIO_RESULT_BLOCKED,
    ERROR_UNSUPPORTED_ADAPTER,
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

    # Write intent detection (Phase 9.3 - with UUID extraction)
    # Supports English and Chinese keywords
    if any(word in prompt_lower for word in [
        "change state", "update status", "mark as", "set state", "move to",
        "update_work_item_state",
        "状态改为", "状态更改为", "改为", "状态设为",
    ]):
        # Extract UUIDs from prompt
        import re
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        uuids = re.findall(uuid_pattern, prompt_lower)
        params = {"prompt": prompt}
        if len(uuids) >= 1:
            params["issue_id"] = uuids[0]
        if len(uuids) >= 2:
            params["proposed_state_id"] = uuids[1]
        return {"tool_name": "update_work_item_state", "params": params}

    # Create work item intent detection (Phase 9.5B-R3)
    if any(word in prompt_lower for word in [
        "新增", "创建", "新建", "create work item", "create issue",
        "add a work item", "add an issue",
    ]):
        import re
        # Try to extract title from prompt patterns like:
        # "命名为 xxx" / "名为 xxx" / "title xxx"
        title = None
        title_match = re.search(r'(?:命名为|名为|title[:\s]*)["“]?([^"”]+)["”]?', prompt)
        if title_match:
            title = title_match.group(1).strip()
        params = {"prompt": prompt}
        if title:
            params["title"] = title
        return {"tool_name": "create_work_item", "params": params}

    # Default: not recognized as an MCP tool request
    return {"tool_name": None, "params": {}}


def _get_adapter_type() -> str:
    """Read AI_MCP_ADAPTER from env. Default: 'mock'."""
    return os.environ.get("AI_MCP_ADAPTER", "mock").strip().lower()


def _serialize_user_safe(user) -> Dict[str, Any]:
    """
    Return only safe fields from a Django User object.
    Never returns password, token, session, auth internals, or API key info.
    """
    result: Dict[str, Any] = {"id": str(user.id)}
    # Include display name if available
    first = getattr(user, "first_name", "")
    last = getattr(user, "last_name", "")
    if first or last:
        result["display_name"] = f"{first} {last}".strip()
    # Include email — Plane's get_me API returns it
    email = getattr(user, "email", "")
    if email:
        result["email"] = email
    return result


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
    - get_me: NEVER uses MCP result. Returns request.user safe fields.
    - list_projects: NEVER uses MCP result fields. Uses local DB for safe fields.
    - retrieve_project: NEVER uses MCP result fields. Uses local DB for safe fields.
    - All other tools: blocked (return error)

    SECURITY: raw MCP result is NEVER returned to the frontend.
    """

    # --- get_me: always from request.user, never from MCP ---
    if tool_name == "get_me":
        # Intentionally ignores MCP result. Returns current Plane session user,
        # not the API-key owner identity.
        return {
            "success": True,
            "result": _serialize_user_safe(user),
        }

    # --- list_projects: local DB only, never MCP fields ---
    if tool_name == "list_projects":
        try:
            # Query accessible projects from local DB (same as mock adapter)
            projects = _get_accessible_projects_qs(user, workspace_slug).values(
                "id", "name", "identifier", "description"
            )[:50]
            project_list = [
                {
                    "id": str(p["id"]),
                    "name": p["name"],
                    "identifier": p["identifier"],
                    "description": p["description"],
                }
                for p in projects
            ]
            return {"success": True, "result": {"projects": project_list, "count": len(project_list)}}
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


def _generate_proposed_action(
    tool_name: str,
    workspace_slug: str,
    user,
    params: Optional[Dict] = None,
) -> Optional[Dict[str, Any]]:
    """
    Generate a proposed_action for write operations (Phase 9.3).

    Validates issue/state exist, belong to workspace/project, and user has permission.
    Returns proposed_action with execution_enabled=True if all checks pass.
    Returns proposed_action with execution_enabled=False if validation fails.
    Never executes real write operations.
    """
    import uuid
    import json
    from datetime import timedelta
    from django.core.signing import TimestampSigner
    from django.utils import timezone
    from plane.db.models import Issue, State, Project, ProjectMember, WorkspaceMember

    if tool_name not in ("update_work_item_state", "create_work_item"):
        return None

    params = params or {}
    actor_id = str(user.id) if user else None

    # === create_work_item ===
    if tool_name == "create_work_item":
        title = params.get("title", "")
        prompt = params.get("prompt", "")

        # Try to extract title from prompt if not provided
        if not title:
            import re
            title_match = re.search(r'(?:命名为|名为|title[:\s]*)["\']?([^"\']+)["\']?', prompt)
            if title_match:
                title = title_match.group(1).strip()
        if not title:
            title = "New work item"

        # Find the first project in the workspace the user can access
        project = None
        project_name = None
        projects_qs = _get_accessible_projects_qs(user, workspace_slug)
        first_project = projects_qs.first()
        if first_project:
            project = first_project
            project_name = first_project.name

        if not project:
            return {
                "action_id": str(uuid.uuid4()),
                "workspace_slug": workspace_slug,
                "actor_id": actor_id,
                "action_type": "create_work_item",
                "target_type": "work_item",
                "target_id": None,
                "target_display": title,
                "project": None,
                "proposed_value": title,
                "risk_level": "medium",
                "summary": f"Create work item: {title}",
                "requires_confirmation": True,
                "expires_at": (timezone.now() + timedelta(minutes=5)).isoformat(),
                "execution_enabled": False,
                "confirmation_token": None,
            }

        # Generate signed confirmation token
        signer = TimestampSigner()
        token_payload = json.dumps({
            "action_id": str(uuid.uuid4()),
            "workspace_slug": workspace_slug,
            "actor_id": actor_id,
            "project_id": str(project.id),
            "title": title,
            "action_type": "create_work_item",
        })
        action_id = str(uuid.uuid4())
        token_payload_dict = json.loads(token_payload)
        token_payload_dict["action_id"] = action_id
        confirmation_token = signer.sign(json.dumps(token_payload_dict))

        create_ai_audit_event(
            event="ai.write.proposed",
            workspace_slug=workspace_slug,
            actor_id=actor_id,
            mode="mcp",
            tool_name="create_work_item",
            tool_status="proposed",
            readonly=False,
            write_operation=True,
        )

        return {
            "action_id": action_id,
            "workspace_slug": workspace_slug,
            "actor_id": actor_id,
            "action_type": "create_work_item",
            "target_type": "work_item",
            "target_id": None,
            "target_display": title,
            "project": {"id": str(project.id), "name": project_name},
            "proposed_value": title,
            "risk_level": "medium",
            "summary": f"Create work item: {title}",
            "requires_confirmation": True,
            "expires_at": (timezone.now() + timedelta(minutes=5)).isoformat(),
            "execution_enabled": True,
            "confirmation_token": confirmation_token,
        }

    # === update_work_item_state ===
    issue_id = params.get("issue_id")
    proposed_state_id = params.get("proposed_state_id")

    # Base proposed_action (plan-only fallback)
    base_action = {
        "action_id": str(uuid.uuid4()),
        "workspace_slug": workspace_slug,
        "actor_id": actor_id,
        "action_type": "update_work_item_state",
        "target_type": "work_item",
        "target_id": issue_id,
        "target_display": None,
        "current_value": None,
        "proposed_value": None,
        "risk_level": "medium",
        "summary": "Update work item state",
        "requires_confirmation": True,
        "expires_at": (timezone.now() + timedelta(minutes=5)).isoformat(),
        "execution_enabled": False,
        "confirmation_token": None,
    }

    # If no issue_id or state_id provided, return plan-only
    if not issue_id or not proposed_state_id:
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
        return base_action

    # Validate UUIDs
    try:
        uuid.UUID(issue_id)
        uuid.UUID(proposed_state_id)
    except (ValueError, TypeError):
        return base_action

    # Validate workspace membership
    if not WorkspaceMember.objects.filter(
        workspace__slug=workspace_slug, member=user, is_active=True
    ).exists():
        return base_action

    # Validate issue exists and belongs to workspace
    try:
        issue = Issue.objects.get(pk=issue_id, workspace__slug=workspace_slug)
    except (Issue.DoesNotExist, ValueError):
        return base_action

    # Validate project membership (ADMIN or MEMBER)
    if not ProjectMember.objects.filter(
        project_id=issue.project_id,
        member=user,
        role__in=[20, 15],  # ADMIN, MEMBER
        is_active=True,
    ).exists():
        return base_action

    # Validate proposed state belongs to same project
    try:
        proposed_state = State.objects.get(pk=proposed_state_id, project_id=issue.project_id)
    except (State.DoesNotExist, ValueError):
        return base_action

    # Get current state name
    current_state = None
    if issue.state_id:
        try:
            current_state = State.objects.get(pk=issue.state_id)
        except State.DoesNotExist:
            pass

    # Generate signed confirmation token
    signer = TimestampSigner()
    token_payload = json.dumps({
        "action_id": base_action["action_id"],
        "workspace_slug": workspace_slug,
        "actor_id": actor_id,
        "issue_id": issue_id,
        "project_id": str(issue.project_id),
        "current_state_id": str(issue.state_id) if issue.state_id else None,
        "proposed_state_id": proposed_state_id,
        "action_type": "update_work_item_state",
    })
    confirmation_token = signer.sign(token_payload)

    # All validations passed - build enabled proposed_action
    proposed_action = {
        **base_action,
        "target_display": issue.name[:100] if issue.name else str(issue_id),
        "current_value": current_state.name if current_state else None,
        "proposed_value": proposed_state.name,
        "summary": f"Update state: {current_state.name if current_state else '?'} → {proposed_state.name}",
        "execution_enabled": True,
        "confirmation_token": confirmation_token,
    }

    # Log audit event
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
        create_ai_audit_event(
            event="ai.tool.blocked",
            workspace_slug=workspace_slug,
            actor_id=str(user.id) if user else None,
            mode="mcp",
            error_code=ERROR_MCP_RUNTIME_DISABLED,
        )
        return {
            "success": False,
            "error": "MCP runtime is not enabled. Set ENABLE_AI_MCP_RUNTIME=1 to enable.",
            "mode": "mcp",
        }

    # Parse intent
    intent = parse_mcp_intent(prompt)
    tool_name = intent.get("tool_name")

    if not tool_name:
        create_ai_audit_event(
            event="ai.tool.blocked",
            workspace_slug=workspace_slug,
            actor_id=str(user.id) if user else None,
            mode="mcp",
            error_code=ERROR_TOOL_NOT_ALLOWED,
        )
        return {
            "success": False,
            "error": "Could not determine which MCP tool to call. Try asking about projects, work items, states, labels, cycles, or modules.",
            "mode": "mcp",
            "available_tools": [get_tool_description(t) for t in READ_ONLY_TOOLS],
        }

    # Validate tool is allowed
    if not is_tool_allowed(tool_name):
        # Phase 9.3: Check if this is a write operation that can generate proposed_action
        proposed_action = _generate_proposed_action(
            tool_name=tool_name,
            workspace_slug=workspace_slug,
            user=user,
            params=intent.get("params"),
        )
        if proposed_action:
            return {
                "success": True,
                "mode": "mcp",
                "adapter": _get_adapter_type(),
                "tool": tool_name,
                "tool_description": "Write operation proposed (plan only)",
                "result": {},
                "proposed_action": proposed_action,
            }

        create_ai_audit_event(
            event="ai.tool.rejected",
            workspace_slug=workspace_slug,
            actor_id=str(user.id) if user else None,
            mode="mcp",
            tool_name=tool_name,
            tool_status="rejected",
            write_operation=True,
            error_code=ERROR_TOOL_NOT_ALLOWED,
        )
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
            create_ai_audit_event(
                event="ai.tool.blocked",
                workspace_slug=workspace_slug,
                actor_id=str(user.id) if user else None,
                mode="mcp",
                adapter="stdio",
                tool_name=tool_name,
                tool_status="blocked",
                error_code=ERROR_STDIO_RESULT_BLOCKED,
            )
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
        create_ai_audit_event(
            event="ai.tool.blocked",
            workspace_slug=workspace_slug,
            actor_id=str(user.id) if user else None,
            mode="mcp",
            adapter=adapter,
            error_code=ERROR_UNSUPPORTED_ADAPTER,
        )
        return {
            "success": False,
            "mode": "mcp",
            "error": f"Unsupported AI_MCP_ADAPTER value: '{adapter}'. Use 'mock' or 'stdio'.",
        }


def build_mcp_preview(mcp_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a structured, safe MCP preview for the frontend.

    Never returns raw MCP result, stack traces, env vars, or secrets.
    """
    tool = mcp_result.get("tool", "unknown")
    success = mcp_result.get("success", False)
    adapter = mcp_result.get("adapter", "unknown")
    error = mcp_result.get("error")
    result = mcp_result.get("result", {})

    # Determine status
    if not success:
        status = "blocked" if "not available" in (error or "").lower() else "error"
    else:
        status = "success"

    # Build items from result
    items: list = []
    summary = ""

    if success and result:
        if tool == "get_me":
            name = result.get("display_name", "")
            email = result.get("email", "")
            uid = result.get("id") or result.get("user_id", "")
            items.append({
                "type": "user",
                "title": name or uid,
                "subtitle": email,
                "metadata": {"id": uid},
            })
            summary = name or email or f"User {uid}"

        elif tool == "list_projects":
            projects = result.get("projects", [])
            count = result.get("count", len(projects))
            summary = f"{count} project(s)"
            for p in projects[:10]:
                items.append({
                    "type": "project",
                    "title": p.get("name", ""),
                    "subtitle": p.get("identifier", ""),
                    "metadata": {"id": p.get("id", "")},
                })

        elif tool == "retrieve_project":
            items.append({
                "type": "project",
                "title": result.get("name", ""),
                "subtitle": result.get("identifier", ""),
                "metadata": {"id": result.get("id", "")},
            })
            summary = result.get("name", "Project")

        elif tool in ("list_work_items", "search_work_items"):
            work_items = result.get("work_items", [])
            count = result.get("count", len(work_items))
            summary = f"{count} work item(s)"
            for wi in work_items[:10]:
                items.append({
                    "type": "work_item",
                    "title": wi.get("name", ""),
                    "subtitle": wi.get("state__name") or wi.get("priority", ""),
                    "metadata": {"id": wi.get("id", "")},
                })

        elif tool == "retrieve_work_item":
            items.append({
                "type": "work_item",
                "title": result.get("name", ""),
                "subtitle": result.get("state") or result.get("priority", ""),
                "metadata": {"id": result.get("id", "")},
            })
            summary = result.get("name", "Work item")

        elif tool == "list_states":
            states = result.get("states", [])
            count = result.get("count", len(states))
            summary = f"{count} state(s)"
            for s in states[:10]:
                items.append({
                    "type": "state",
                    "title": s.get("name", ""),
                    "subtitle": s.get("group", ""),
                    "metadata": {"id": s.get("id", ""), "color": s.get("color", "")},
                })

        elif tool == "list_labels":
            labels = result.get("labels", [])
            count = result.get("count", len(labels))
            summary = f"{count} label(s)"
            for l in labels[:10]:
                items.append({
                    "type": "label",
                    "title": l.get("name", ""),
                    "subtitle": "",
                    "metadata": {"id": l.get("id", ""), "color": l.get("color", "")},
                })

        elif tool == "list_cycles":
            cycles = result.get("cycles", [])
            count = result.get("count", len(cycles))
            summary = f"{count} cycle(s)"
            for c in cycles[:10]:
                items.append({
                    "type": "cycle",
                    "title": c.get("name", ""),
                    "subtitle": f"{c.get('start_date', '')} - {c.get('end_date', '')}",
                    "metadata": {"id": c.get("id", "")},
                })

        elif tool == "list_modules":
            modules = result.get("modules", [])
            count = result.get("count", len(modules))
            summary = f"{count} module(s)"
            for m in modules[:10]:
                items.append({
                    "type": "module",
                    "title": m.get("name", ""),
                    "subtitle": m.get("description", "")[:80] if m.get("description") else "",
                    "metadata": {"id": m.get("id", "")},
                })

    if not summary and error:
        summary = error
    if not summary:
        summary = "No results"

    # Check for proposed_action (Phase 9.1 - write confirmation)
    proposed_action = mcp_result.get("proposed_action")
    is_write = proposed_action is not None

    return {
        "mode": "mcp",
        "adapter": adapter,
        "tool": {
            "name": tool,
            "status": "proposed" if is_write else status,
            "readonly": not is_write,
        },
        "summary": proposed_action.get("summary", summary) if is_write else summary,
        "items": items,
        "safety": {
            "raw_result_returned": False,
            "write_operation": is_write,
            "permission_filtered": True,
        },
        "proposed_action": proposed_action,
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
        # Handle both mock format (user_id) and stdio format (id/display_name/email)
        user_id = result.get("id") or result.get("user_id", "")
        name = result.get("display_name", "")
        email = result.get("email", "")
        parts = [f"User ID: {user_id}"]
        if name:
            parts.append(f"Name: {name}")
        if email:
            parts.append(f"Email: {email}")
        return "\n".join(parts)

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
