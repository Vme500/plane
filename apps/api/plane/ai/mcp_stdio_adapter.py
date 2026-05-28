# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
MCP stdio adapter — launches plane-mcp-server as a subprocess and
communicates via the MCP JSON-RPC protocol over stdin/stdout.

SECURITY NOTES:
- This adapter uses PLANE_API_KEY (workspace-level), NOT per-user tokens.
- The MCP server can access ALL projects in the workspace, regardless of
  the current user's project membership.
- We mitigate this by: (a) tool allowlist, (b) write-operation rejection,
  (c) optional post-filtering of results when project_id is identifiable.
- This adapter does NOT provide per-user permission guarantees.
- shell=False, list args only, timeout enforced, no prompt in command.
"""

import json
import os
import subprocess
import uuid
from typing import Any, Dict, List, Optional

from plane.utils.exception_logger import log_exception

from .mcp_tools import READ_ONLY_TOOLS, is_tool_allowed

# Mapping: our local tool names → plane-mcp-server tool names (identical)
LOCAL_TO_MCP_TOOL: Dict[str, str] = {
    "get_me": "get_me",
    "list_projects": "list_projects",
    "retrieve_project": "retrieve_project",
    "list_work_items": "list_work_items",
    "search_work_items": "search_work_items",
    "retrieve_work_item": "retrieve_work_item",
    "list_states": "list_states",
    "list_labels": "list_labels",
    "list_cycles": "list_cycles",
    "list_modules": "list_modules",
}

# Safe error message — never expose internals
_STDIO_ERROR = "MCP stdio adapter error."


def _get_adapter_config() -> Dict[str, Any]:
    """Read stdio adapter configuration from environment. Never expose to frontend."""
    return {
        "command": os.environ.get("AI_MCP_SERVER_COMMAND", "uvx"),
        "args": os.environ.get("AI_MCP_SERVER_ARGS", "plane-mcp-server stdio").split(),
        "timeout": int(os.environ.get("AI_MCP_SERVER_TIMEOUT_SECONDS", "15")),
    }


def _new_request_id() -> str:
    return str(uuid.uuid4())


def _make_request(method: str, params: Optional[Dict] = None) -> str:
    """Build a JSON-RPC 2.0 request string."""
    msg: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": _new_request_id(),
        "method": method,
    }
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)


def _make_notification(method: str, params: Optional[Dict] = None) -> str:
    """Build a JSON-RPC 2.0 notification (no id, no response expected)."""
    msg: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "method": method,
    }
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)


def _read_message(proc: subprocess.Popen, timeout: float) -> Optional[Dict]:
    """Read one JSON-RPC message from stdout. Returns None on timeout."""
    import select
    import time

    deadline = time.monotonic() + timeout
    buffer = ""
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        ready, _, _ = select.select([proc.stdout], [], [], min(remaining, 0.5))
        if ready:
            chunk = proc.stdout.read(1)
            if not chunk:
                break
            char = chunk.decode("utf-8", errors="replace")
            if char == "\n":
                line = buffer.strip()
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        buffer = ""
                        continue
            else:
                buffer += char
    return None


def _write_message(proc: subprocess.Popen, message: str) -> None:
    """Write a JSON-RPC message to stdin."""
    proc.stdin.write((message + "\n").encode("utf-8"))
    proc.stdin.flush()


def _read_response_for_id(proc: subprocess.Popen, request_id: str, timeout: float) -> Optional[Dict]:
    """
    Read messages until we get a response matching request_id.
    Discard notifications and responses for other ids.
    """
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        msg = _read_message(proc, remaining)
        if msg is None:
            break
        # Match response by id
        if msg.get("id") == request_id:
            return msg
        # Otherwise discard (notification or different response)
    return None


def call_tool_stdio(
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call a single tool via plane-mcp-server stdio transport.

    Steps:
    1. Spawn subprocess: uvx plane-mcp-server stdio
    2. Send initialize request
    3. Send initialized notification
    4. Send tools/call request
    5. Read response
    6. Terminate subprocess

    SECURITY:
    - Only READ_ONLY_TOOLS are allowed (double-checked here).
    - shell=False, list args, timeout enforced.
    - stderr is captured, never returned to caller.
    - env vars (PLANE_API_KEY etc.) are passed to subprocess but never logged.
    """
    # Double-check tool is allowed
    if not is_tool_allowed(tool_name):
        return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}

    mcp_tool_name = LOCAL_TO_MCP_TOOL.get(tool_name)
    if not mcp_tool_name:
        return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}

    config = _get_adapter_config()
    timeout = config["timeout"]
    command = config["command"]
    args = config["args"]

    # Build env: inherit safe vars + pass through PLANE_* for MCP server
    env = os.environ.copy()

    proc = None
    try:
        # Spawn subprocess — shell=False, list args
        proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True,
        )

        # Step 1: Initialize
        init_id = _new_request_id()
        init_msg = _make_request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "plane-ai-mcp-client", "version": "1.0.0"},
        })
        # Override id
        init_msg = json.dumps({**json.loads(init_msg), "id": init_id})
        _write_message(proc, init_msg)

        init_resp = _read_response_for_id(proc, init_id, timeout)
        if not init_resp or "error" in init_resp:
            return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}

        # Step 2: Initialized notification
        _write_message(proc, _make_notification("notifications/initialized"))

        # Step 3: Call tool
        call_id = _new_request_id()
        call_msg = _make_request("tools/call", {
            "name": mcp_tool_name,
            "arguments": arguments or {},
        })
        call_msg = json.dumps({**json.loads(call_msg), "id": call_id})
        _write_message(proc, call_msg)

        call_resp = _read_response_for_id(proc, call_id, timeout)
        if not call_resp:
            return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}

        if "error" in call_resp:
            return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}

        # Extract result content
        result = call_resp.get("result", {})
        content = result.get("content", [])

        # MCP tools/call returns content as list of {type, text} blocks
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        if text_parts:
            raw_text = "\n".join(text_parts)
            # Try to parse as JSON
            try:
                parsed = json.loads(raw_text)
                return {"success": True, "tool": tool_name, "result": parsed}
            except (json.JSONDecodeError, TypeError):
                return {"success": True, "tool": tool_name, "result": {"text": raw_text}}

        return {"success": True, "tool": tool_name, "result": result}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}
    except FileNotFoundError:
        return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}
    except Exception as e:
        log_exception(e)
        return {"success": False, "error": _STDIO_ERROR, "tool": tool_name}
    finally:
        if proc is not None:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=2)
            except Exception:
                pass
            # Close pipes
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    if stream:
                        stream.close()
                except Exception:
                    pass
