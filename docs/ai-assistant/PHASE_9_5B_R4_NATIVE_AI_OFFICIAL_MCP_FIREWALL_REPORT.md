# Phase 9.5B-R4: Native AI Official MCP Route Firewall

> **Status**: ✅ Complete
> **Date**: 2026-06-11
> **Commit**: `259ffe372c` — fix: enforce native AI official MCP route firewall
> **Branch**: `feat/ai-phase-6-mcp-readonly-runtime`

---

## 1. Why Route Firewall

Native AI Drawer 是 Plane AI 的主入口。风险在于：native endpoint 可能意外回流到 legacy `mcp_runtime` / pi-ai parser，导致：

- 绕过 official MCP gateway 的 tool 权限控制
- 泄露 `confirmation_token` 到前端
- 执行未经审计的 write 操作
- 与 `/pi-chat` legacy 路线产生隐式耦合

Route firewall 确保 native 路线与 legacy 完全隔离。

## 2. Legacy Route-back Risk (Before 9.5B-R4)

| 风险                           | 描述                        |
| ------------------------------ | --------------------------- |
| Drawer → createGptTask         | 前端可能调用旧的 AI service |
| Drawer → /ai-assistant/        | 前端可能调用旧 endpoint     |
| ai_native.py → mcp_runtime     | 后端可能 import legacy 模块 |
| mcp_runtime 被 native 路线使用 | 间接依赖导致隔离失效        |

## 3. Changes in 9.5B-R4

### 3.1 New Files

| File                                                     | Purpose                                                       |
| -------------------------------------------------------- | ------------------------------------------------------------- |
| `apps/api/plane/app/views/ai_native.py` (215 lines)      | Native AI endpoint — only routes through official MCP gateway |
| `apps/web/core/services/native-ai.service.ts` (32 lines) | Frontend service for native AI endpoints                      |
| `scripts/check_native_ai_route_firewall.py` (128 lines)  | Automated route firewall check script                         |

### 3.2 Modified Files

| File                                                                 | Change                                                         |
| -------------------------------------------------------------------- | -------------------------------------------------------------- |
| `apps/api/plane/ai/mcp_gateway.py`                                   | +25 lines — enhanced gateway support                           |
| `apps/api/plane/app/urls/external.py`                                | +11 lines — registered native AI routes                        |
| `apps/web/core/components/workspace/sidebar/ai-assistant-drawer.tsx` | +86/-33 — switched to NativeAIService, added source validation |

### 3.3 Backend: mcp_runtime.py

+5 lines (minor). `mcp_runtime.py` is NOT imported by any native AI file.

## 4. Native AI Endpoint Paths

| Endpoint | Method | Path                                                  |
| -------- | ------ | ----------------------------------------------------- |
| Status   | GET    | `/api/workspaces/<slug>/ai-assistant/native/status/`  |
| Propose  | POST   | `/api/workspaces/<slug>/ai-assistant/native/propose/` |

## 5. Legacy Isolation Verification

| Check                                                  | Result                                           |
| ------------------------------------------------------ | ------------------------------------------------ |
| Drawer stops calling `createGptTask`                   | ✅ Yes                                           |
| Drawer stops calling old `/ai-assistant/` endpoint     | ✅ Yes                                           |
| Native backend stops importing `mcp_runtime`           | ✅ Yes                                           |
| Native backend only uses `mcp_gateway`                 | ✅ Yes                                           |
| Response `source` field = `official_mcp_gateway`       | ✅ Yes                                           |
| Frontend validates `source === "official_mcp_gateway"` | ✅ Yes                                           |
| `confirmation_token` NOT returned to frontend          | ✅ Yes (only `confirmation_token_present: bool`) |

## 6. Route Firewall Script

**File**: `scripts/check_native_ai_route_firewall.py`

Checks performed:

1. Native backend files do NOT import `mcp_runtime`
2. Native frontend files do NOT use `createGptTask`, `new AIService()`, or `/ai-test/pi-chat`
3. Native endpoint returns `source: "official_mcp_gateway"`
4. Frontend validates `source === "official_mcp_gateway"`

**Result**: ✅ All checks passed. Native AI route is isolated from legacy.

## 7. Current Legacy mcp_runtime Status

`mcp_runtime.py` still exists in the codebase but is NOT imported or used by any native AI file. It remains for potential legacy `/pi-chat` compatibility only.

## 8. Validation Results

| Criterion           | Value |
| ------------------- | ----- |
| `asdfg` count       | 0     |
| `ai.write.executed` | 1     |
| Clicked Confirm     | No    |
| Created `asdfg`     | No    |
| Affected 18080      | No    |
| Secrets leaked      | No    |
| Pushed to origin    | Yes   |
| PR created          | No    |

## 9. Next Step

**Phase 9.5B-R5**: Native proposed-only UI re-verification — confirm end-to-end native Drawer → official MCP gateway → proposed_action card rendering in dev stack.
