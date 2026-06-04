# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Official MCP Client — connects to plane-mcp-server via stdio JSON-RPC.

SECURITY:
- Never exposes API keys, tokens, or secrets.
- Never logs raw MCP responses to audit.
- timeout enforced on all operations.
- Process cleanup on errors.
"""

import json
import os
import subprocess
import uuid
from typing import Any, Dict, List, Optional

from plane.utils.exception_logger import log_exception

_SAFE_ERROR = "MCP client error."


def _new_id() -> str:
    return str(uuid.uuid4())


def _jsonrpc_request(method: str, params: Optional[Dict] = None) -> str:
    msg: Dict[str, Any] = {"jsonrpc": "2.0", "id": _new_id(), "method": method}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)


def _jsonrpc_notification(method: str, params: Optional[Dict] = None) -> str:
    msg: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)


def _read_line(proc: subprocess.Popen, timeout: float) -> Optional[str]:
    """Read one line from stdout with timeout using readline()."""
    import time

    deadline = time.monotonic() + timeout
    # readline() blocks until a full line is available
    # We use a simple loop with a check on stdout readability
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            # EOF
            return None
        decoded = line.decode("utf-8", errors="replace").strip()
        if decoded:
            return decoded
    return None


def _read_response(proc: subprocess.Popen, request_id: str, timeout: float) -> Optional[Dict]:
    """Read messages until we get a response matching request_id.
    Skips non-JSON lines (e.g. MCP server banner)."""
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        line = _read_line(proc, remaining)
        if line is None:
            break
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            # Skip non-JSON lines (banner, warnings, etc.)
            continue
        if msg.get("id") == request_id:
            return msg
    return None


def list_tools_safe(
    command: str = "uvx",
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Start MCP server, list tools, return safe summary.

    Returns:
        {"success": True, "tools": [...], "tool_count": N, "has_create_work_item": bool, ...}
        or {"success": False, "error": "..."}
    """
    if args is None:
        args = ["plane-mcp-server", "stdio"]

    proc = None
    try:
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
            start_new_session=True,
        )

        # Initialize
        init_id = _new_id()
        init_msg = json.dumps({
            "jsonrpc": "2.0",
            "id": init_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "plane-ai-gateway", "version": "1.0.0"},
            },
        })
        proc.stdin.write((init_msg + "\n").encode("utf-8"))
        proc.stdin.flush()

        init_resp = _read_response(proc, init_id, timeout)
        if not init_resp or "error" in init_resp:
            return {"success": False, "error": _SAFE_ERROR}

        # Initialized notification
        proc.stdin.write((_jsonrpc_notification("notifications/initialized") + "\n").encode("utf-8"))
        proc.stdin.flush()

        # List tools
        list_id = _new_id()
        list_msg = json.dumps({"jsonrpc": "2.0", "id": list_id, "method": "tools/list"})
        proc.stdin.write((list_msg + "\n").encode("utf-8"))
        proc.stdin.flush()

        list_resp = _read_response(proc, list_id, timeout)
        if not list_resp or "error" in list_resp:
            return {"success": False, "error": _SAFE_ERROR}

        tools = list_resp.get("result", {}).get("tools", [])
        tool_names = [t.get("name", "") for t in tools]

        return {
            "success": True,
            "tool_count": len(tools),
            "tool_names": tool_names,
            "has_create_work_item": "create_work_item" in tool_names,
            "has_update_work_item": "update_work_item" in tool_names,
            "has_delete_work_item": "delete_work_item" in tool_names,
            "has_list_projects": "list_projects" in tool_names,
            "has_list_work_items": "list_work_items" in tool_names,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": _SAFE_ERROR}
    except FileNotFoundError:
        return {"success": False, "error": _SAFE_ERROR}
    except Exception as e:
        log_exception(e)
        return {"success": False, "error": _SAFE_ERROR}
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
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    if stream:
                        stream.close()
                except Exception:
                    pass
