# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
AI/MCP Audit Logger — structured safe audit events via Python logging.

SECURITY:
- NEVER logs raw prompt, raw result, raw MCP result, or secrets.
- NEVER logs request headers, stack trace, env, token, API key, cookie, password.
- Only logs safe metadata fields (see ALLOWED_FIELDS).
- Errors are code-ified, never raw exception messages.

Usage:
    from plane.ai.audit_logger import log_ai_event
    log_ai_event(event="ai.request", workspace_slug=slug, user_id=uid, mode="mcp")
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("plane.ai.audit")

# Safe error codes — never raw exception messages
ERROR_INVALID_MODE = "invalid_mode"
ERROR_MCP_RUNTIME_DISABLED = "mcp_runtime_disabled"
ERROR_UNSUPPORTED_ADAPTER = "unsupported_adapter"
ERROR_TOOL_NOT_ALLOWED = "tool_not_allowed"
ERROR_WRITE_REJECTED = "write_operation_rejected"
ERROR_STDIO_TIMEOUT = "stdio_timeout"
ERROR_STDIO_START_FAILED = "stdio_start_failed"
ERROR_STDIO_PERMISSION_GATE = "stdio_permission_gate"
ERROR_STDIO_RESULT_BLOCKED = "stdio_result_blocked"
ERROR_MCP_TOOL_ERROR = "mcp_tool_error"
ERROR_LLM_REQUEST_ERROR = "llm_request_error"
ERROR_UNKNOWN = "unknown_error"


def log_ai_event(
    *,
    event: str,
    workspace_slug: Optional[str] = None,
    user_id: Optional[str] = None,
    mode: Optional[str] = None,
    adapter: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_status: Optional[str] = None,
    readonly: bool = True,
    permission_filtered: Optional[bool] = None,
    raw_result_returned: bool = False,
    write_operation: bool = False,
    duration_ms: Optional[int] = None,
    item_count: Optional[int] = None,
    error_code: Optional[str] = None,
    prompt_length: Optional[int] = None,
    source: str = "pi-chat",
) -> None:
    """
    Log a structured AI/MCP audit event.

    All fields are optional except `event`. Unknown or unsafe fields are
    silently ignored — only ALLOWED_FIELDS are included in the log output.
    """
    record: dict = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "readonly": readonly,
        "raw_result_returned": raw_result_returned,
        "write_operation": write_operation,
        "source": source,
    }

    # Only add fields that are not None
    if workspace_slug is not None:
        record["workspace_slug"] = workspace_slug
    if user_id is not None:
        record["user_id"] = user_id
    if mode is not None:
        record["mode"] = mode
    if adapter is not None:
        record["adapter"] = adapter
    if tool_name is not None:
        record["tool_name"] = tool_name
    if tool_status is not None:
        record["tool_status"] = tool_status
    if permission_filtered is not None:
        record["permission_filtered"] = permission_filtered
    if duration_ms is not None:
        record["duration_ms"] = duration_ms
    if item_count is not None:
        record["item_count"] = item_count
    if error_code is not None:
        record["error_code"] = error_code
    if prompt_length is not None:
        record["prompt_length"] = prompt_length

    logger.info(json.dumps(record, default=str))


def safe_error_code(error: Optional[str]) -> str:
    """Map a known error message to a safe error code. Falls back to unknown_error."""
    if not error:
        return ERROR_UNKNOWN
    error_lower = error.lower()
    if "not enabled" in error_lower or "not set" in error_lower:
        return ERROR_MCP_RUNTIME_DISABLED
    if "not allowed" in error_lower or "read-only" in error_lower:
        return ERROR_TOOL_NOT_ALLOWED
    if "blocked" in error_lower or "not available" in error_lower:
        return ERROR_STDIO_RESULT_BLOCKED
    if "permission" in error_lower or "access denied" in error_lower:
        return ERROR_STDIO_PERMISSION_GATE
    if "timeout" in error_lower:
        return ERROR_STDIO_TIMEOUT
    if "unsupported" in error_lower:
        return ERROR_UNSUPPORTED_ADAPTER
    if "invalid" in error_lower and "mode" in error_lower:
        return ERROR_INVALID_MODE
    return ERROR_UNKNOWN


def now_ms() -> float:
    """Return current time in milliseconds (for duration calculation)."""
    return time.monotonic() * 1000


def duration_since(start_ms: float) -> int:
    """Return elapsed milliseconds since start_ms."""
    return int(time.monotonic() * 1000 - start_ms)


def create_ai_audit_event(
    *,
    workspace_slug: str,
    actor_id: Optional[str],
    event: str,
    mode: Optional[str] = None,
    adapter: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_status: Optional[str] = None,
    readonly: bool = True,
    permission_filtered: Optional[bool] = None,
    raw_result_returned: bool = False,
    write_operation: bool = False,
    duration_ms: Optional[int] = None,
    item_count: Optional[int] = None,
    prompt_length: Optional[int] = None,
    error_code: Optional[str] = None,
    source: str = "pi-chat",
    request_id: Optional[str] = None,
) -> None:
    """
    Persist an AI audit event to the database. Fail-safe: never raises.

    Calls log_ai_event() for structured logging AND attempts DB write.
    DB write failure is silently logged to the server logger, never to the client.
    """
    # Always log to structured logger first
    log_ai_event(
        event=event,
        workspace_slug=workspace_slug,
        user_id=actor_id,
        mode=mode,
        adapter=adapter,
        tool_name=tool_name,
        tool_status=tool_status,
        readonly=readonly,
        permission_filtered=permission_filtered,
        raw_result_returned=raw_result_returned,
        write_operation=write_operation,
        duration_ms=duration_ms,
        item_count=item_count,
        error_code=error_code,
        source=source,
    )

    # Attempt DB write — fail-safe
    try:
        from plane.db.models import AIAuditEvent, Workspace

        workspace = Workspace.objects.filter(slug=workspace_slug).first()
        if not workspace:
            return

        AIAuditEvent.objects.create(
            workspace=workspace,
            actor_id=actor_id if actor_id else None,
            event=event,
            mode=mode,
            adapter=adapter,
            tool_name=tool_name,
            tool_status=tool_status,
            readonly=readonly,
            permission_filtered=permission_filtered,
            raw_result_returned=raw_result_returned,
            write_operation=write_operation,
            duration_ms=duration_ms,
            item_count=item_count,
            prompt_length=prompt_length,
            error_code=error_code,
            source=source,
            request_id=request_id,
        )
    except Exception as e:
        # DB write failure must not affect AI/MCP main flow
        logger.warning(f"Failed to persist AI audit event: {type(e).__name__}")
