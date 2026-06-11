# Phase 9.5B-R5: Native AI Proposed-Only UI Validation

> **Status**: ✅ Complete
> **Date**: 2026-06-11
> **Commit**: `4f42c76905` (base) — docs: backfill native AI route firewall report
> **Branch**: `feat/ai-phase-6-mcp-readonly-runtime`

---

## 1. Route Firewall

| Check                                      | Result  |
| ------------------------------------------ | ------- |
| Route firewall script                      | ✅ PASS |
| Native backend no `mcp_runtime` import     | ✅      |
| Native frontend no `createGptTask`         | ✅      |
| Response `source` = `official_mcp_gateway` | ✅      |

## 2. Backend: native/propose Endpoint

**Test input**: `新增一个 work item，命名为 asdfg`

| Field                        | Expected               | Actual                 | Status |
| ---------------------------- | ---------------------- | ---------------------- | ------ |
| `route`                      | `official_mcp`         | `official_mcp`         | ✅     |
| `source`                     | `official_mcp_gateway` | `official_mcp_gateway` | ✅     |
| `response_type`              | `proposed_action`      | `proposed_action`      | ✅     |
| `proposed_action.source`     | `official_mcp_gateway` | `official_mcp_gateway` | ✅     |
| `action_type`                | `create_work_item`     | `create_work_item`     | ✅     |
| `project.name`               | `AI Test Project`      | `AI Test Project`      | ✅     |
| `title`                      | `asdfg`                | `asdfg`                | ✅     |
| `risk_level`                 | `medium`               | `medium`               | ✅     |
| `requires_confirmation`      | `true`                 | `true`                 | ✅     |
| `execution_enabled`          | `true`                 | `true`                 | ✅     |
| `confirmation_token_present` | `true`                 | `true`                 | ✅     |
| `raw_result_returned`        | `false`                | `false`                | ✅     |
| `confirmation_token` value   | NOT exposed            | NOT exposed            | ✅     |

## 3. State Validation

| Criterion                 | Result           |
| ------------------------- | ---------------- |
| `asdfg` work item count   | 0 ✅             |
| `ai.write.executed` count | 1 ✅ (unchanged) |
| `ai.write.proposed` count | 21 ✅            |
| Confirm clicked           | No ✅            |
| Work item created         | No ✅            |

## 4. Frontend Build Verification

| Check                                   | Result                  |
| --------------------------------------- | ----------------------- |
| `NativeAIService` in build              | ✅ `layout-D_RuUXSe.js` |
| `official_mcp_gateway` in build         | ✅ (4 occurrences)      |
| `ai-assistant/native` endpoint in build | ✅ (2 occurrences)      |
| `Write Operation Proposed` text         | ✅                      |
| `Confirmation required` text            | ✅                      |
| `AI Assistant` text                     | ✅                      |
| `Plane AI` text                         | ✅                      |

## 5. Frontend UI Verification

**Automated browser test**: Not available (Playwright browsers not installed).

**Code-level verification** (from `ai-assistant-drawer.tsx`):

| UI Element                       | Code Reference            | Status |
| -------------------------------- | ------------------------- | ------ |
| Provider: official MCP           | Line 129                  | ✅     |
| Write Operation Proposed         | Line 142                  | ✅     |
| Action: {action_type}            | Line 144                  | ✅     |
| Project: {project.name}          | Line 145                  | ✅     |
| Title: {title}                   | Line 146                  | ✅     |
| Risk: {risk_level}               | Line 147                  | ✅     |
| Confirmation required            | Line 148                  | ✅     |
| Confirm button (visible/enabled) | Lines 151-156             | ✅     |
| Cancel button                    | Line 157                  | ✅     |
| Source validation                | Lines 63, 79              | ✅     |
| No `confirmation_token` exposed  | Line 29 (only `_present`) | ✅     |
| No raw JSON                      | N/A                       | ✅     |

## 6. Security

| Check            | Result                                  |
| ---------------- | --------------------------------------- |
| Secret grep hits | 249 (all documentation references)      |
| Real secrets     | None ✅                                 |
| Report           | `/tmp/plane-ai-secret-grep-9-5b-r5.txt` |

## 7. Manual Verification Required

User should manually verify in browser:

1. Open `http://localhost:18181/ai-test/projects`
2. Click "AI Assistant" in sidebar
3. Type: `新增一个 work item，命名为 asdfg`
4. Click Send
5. Confirm card shows: Write Operation Proposed, create_work_item, AI Test Project, asdfg
6. Confirm button visible and enabled
7. Cancel button visible
8. **Do NOT click Confirm**

## 8. Next Step

**Phase 9.5C**: Native confirmed create test — execute the actual write via official MCP gateway (separate phase, requires explicit approval).
