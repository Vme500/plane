# Phase 9.5B-R7: Dedicated Edge Profile Proposed-Only E2E Validation

> **Status**: ⚠️ Partial — Backend PASS, UI requires manual user verification
> **Date**: 2026-06-11
> **Commit**: (pending)
> **Branch**: `feat/ai-phase-6-mcp-readonly-runtime`

---

## 1. Dedicated Edge Profile

| Field          | Value                                                      |
| -------------- | ---------------------------------------------------------- |
| Profile path   | `%LOCALAPPDATA%\Microsoft\Edge\User Data\PlaneAI-MCP-Test` |
| CDP port       | `9223`                                                     |
| Browser        | Edge 149.0.4022.62                                         |
| CDP accessible | ✅ (from Windows)                                          |
| Playwright CDP | ❌ WSL→Windows port blocked                                |

## 2. Login Status

| Field                      | Value                                        |
| -------------------------- | -------------------------------------------- |
| Page shows                 | Sign up / Sign in page                       |
| Auto-login attempt         | ❌ Failed (React state not updating via CDP) |
| User manual login required | ✅ One-time                                  |

**User action**: Login in dedicated Edge profile with `admin@ai-test.local`, then the proposed card test can proceed.

## 3. Route Firewall

✅ PASS — `scripts/check_native_ai_route_firewall.py`

## 4. Backend Verification (Django Test Client)

All checks performed via `APIClient.force_authenticate`:

| Field                        | Expected               | Actual                 | Status |
| ---------------------------- | ---------------------- | ---------------------- | ------ |
| `route`                      | `official_mcp`         | `official_mcp`         | ✅     |
| `source`                     | `official_mcp_gateway` | `official_mcp_gateway` | ✅     |
| `response_type`              | `proposed_action`      | `proposed_action`      | ✅     |
| `action_type`                | `create_work_item`     | `create_work_item`     | ✅     |
| `project.name`               | `AI Test Project`      | `AI Test Project`      | ✅     |
| `title`                      | `asdfg`                | `asdfg`                | ✅     |
| `risk_level`                 | `medium`               | `medium`               | ✅     |
| `requires_confirmation`      | `true`                 | `true`                 | ✅     |
| `execution_enabled`          | `true`                 | `true`                 | ✅     |
| `confirmation_token_present` | `true`                 | `true`                 | ✅     |
| `raw_result_returned`        | `false`                | `false`                | ✅     |

## 5. State Validation

| Criterion           | Result              |
| ------------------- | ------------------- |
| `asdfg` count       | 0 ✅                |
| `ai.write.executed` | 1 ✅ (unchanged)    |
| `ai.write.proposed` | 24 ✅ (incremented) |

## 6. Code-Level UI Verification

From `ai-assistant-drawer.tsx` (built and deployed):

| UI Element                                     | Code          | Status                      |
| ---------------------------------------------- | ------------- | --------------------------- |
| Provider: official MCP                         | Line 129      | ✅                          |
| Write Operation Proposed                       | Line 142      | ✅                          |
| Action: {action_type}                          | Line 144      | ✅                          |
| Project: {project.name ?? "Unknown project"}   | Line 145      | ✅ (with fallback)          |
| Title: {title ?? target_display ?? "Untitled"} | Line 146      | ✅ (with fallback)          |
| Risk: {risk_level}                             | Line 147      | ✅                          |
| Confirmation required                          | Line 148      | ✅                          |
| Confirm button (bg-blue-600)                   | Lines 151-156 | ✅ (visible on yellow card) |
| Cancel button                                  | Line 157      | ✅                          |
| Source validation                              | Lines 63, 79  | ✅                          |
| No confirmation_token exposed                  | Line 29       | ✅                          |

## 7. Build Verification

| Check                      | Result |
| -------------------------- | ------ |
| `bg-blue-600` in build     | ✅     |
| `Unknown project` fallback | ✅     |
| `Write Operation Proposed` | ✅     |
| `Confirmation required`    | ✅     |

## 8. Limitations

| Limitation                    | Impact                         |
| ----------------------------- | ------------------------------ |
| WSL→Windows CDP blocked       | Cannot run Playwright from WSL |
| React state via CDP           | Auto-login failed              |
| Edge profile needs user login | One-time manual step           |

## 9. User Manual Verification Steps

After logging into the dedicated Edge profile:

1. Navigate to `http://localhost:18181/ai-test/projects`
2. Click "AI Assistant" in sidebar
3. Type: `新增一个 work item，命名为 asdfg`
4. Click Send
5. Verify card shows: Write Operation Proposed, create_work_item, AI Test Project, asdfg
6. Verify Confirm button is blue and visible
7. Verify Cancel button is visible
8. **Do NOT click Confirm**
9. Take screenshot for record

## 10. Security

- Secret grep: ✅ No real secrets
- Report: `/tmp/plane-ai-secret-grep-9-5b-r7.txt`

## 11. Next Step

**Phase 9.5C**: Native confirmed create test — requires explicit user approval before execution.
