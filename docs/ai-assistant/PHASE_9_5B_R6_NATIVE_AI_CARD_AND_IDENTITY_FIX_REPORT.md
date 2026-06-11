# Phase 9.5B-R6: Native AI Card & Identity Fix

> **Status**: ✅ Complete
> **Date**: 2026-06-11
> **Commit**: (pending)
> **Branch**: `feat/ai-phase-6-mcp-readonly-runtime`

---

## 1. Route Firewall

✅ PASS — `scripts/check_native_ai_route_firewall.py`

## 2. Dev Test Identity

| Criterion              | Value                                       |
| ---------------------- | ------------------------------------------- |
| `dev_test_user_exists` | `true` — `admin@ai-test.local`              |
| `login_ready`          | `true` — active, superuser                  |
| `workspace_member`     | `true` — workspace `ai-test`, role=20       |
| `project_permission`   | `true` — project `AI Test Project`, role=20 |
| `mcp_workspace_slug`   | `ai-test`                                   |
| `secret_printed`       | `false`                                     |

## 3. Official MCP Configuration

| Field          | Value                   |
| -------------- | ----------------------- |
| Provider       | `official_plane_mcp`    |
| Configured     | `true`                  |
| Workspace slug | `ai-test`               |
| Base URL       | `http://localhost:8000` |

MCP workspace matches test user workspace ✅

## 4. Dedicated Edge Profile

- Path: `%LOCALAPPDATA%\Microsoft\Edge\User Data\PlaneAI-MCP-Test`
- Remote debugging port: `9223`
- Launched: ✅
- URL: `http://localhost:18181/ai-test/projects`

## 5. Proposed Card UI Root Cause

**Problem 1: Project not showing**

- Root cause: `pa.project` could be `null` if backend project resolution failed
- Fix: Added fallback resolution in `ai_native.py` (lines 135-148) + frontend fallback `pa.project?.name ?? "Unknown project"`

**Problem 2: Confirm button invisible**

- Root cause: `bg-yellow-600` button on `bg-yellow-50` card — same color family, nearly invisible
- Fix: Changed to `bg-blue-600` with `hover:bg-blue-700`, increased padding

## 6. Modified Files

| File                                                                 | Change                                              |
| -------------------------------------------------------------------- | --------------------------------------------------- |
| `apps/web/core/components/workspace/sidebar/ai-assistant-drawer.tsx` | Confirm → blue, Project fallback, always show Title |
| `apps/api/plane/app/views/ai_native.py`                              | Added project resolution fallbacks                  |

## 7. Backend Verification

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

## 8. Build Verification

| Check                               | Result |
| ----------------------------------- | ------ |
| `bg-blue-600` in build              | ✅     |
| `Unknown project` fallback in build | ✅     |
| `Write Operation Proposed` in build | ✅     |
| `Confirmation required` in build    | ✅     |

## 9. State Validation

| Criterion           | Result |
| ------------------- | ------ |
| `asdfg` count       | 0 ✅   |
| `ai.write.executed` | 1 ✅   |
| Confirm clicked     | No ✅  |
| Work item created   | No ✅  |

## 10. Security

- Secret grep: 254 hits (all documentation references)
- Real secrets: None ✅
- Report: `/tmp/plane-ai-secret-grep-9-5b-r6.txt`

## 11. Next Step

**Phase 9.5B-R7**: Dedicated Edge profile proposed-only UI verification — user completes one-time login in dedicated Edge profile, then verifies proposed card rendering.
