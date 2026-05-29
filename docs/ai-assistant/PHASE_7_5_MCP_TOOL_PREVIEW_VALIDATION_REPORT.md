# 第 7.5 阶段报告：MCP Tool Preview API Contract Validation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：验证完成，无需修复

---

## 1. 当前分支和 commit

| 项目        | 值                                             |
| ----------- | ---------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`         |
| 最新 commit | `351d18c9f9` — `feat: add MCP tool preview UI` |
| 工作区状态  | 干净（无未提交修改）                           |

---

## 2. mcp_preview contract 检查结果

| 字段                         | 存在 | 类型    | 说明                                  |
| ---------------------------- | ---- | ------- | ------------------------------------- |
| `mode`                       | ✅   | string  | `"mcp"`                               |
| `adapter`                    | ✅   | string  | `"mock"` 或 `"stdio"`                 |
| `tool.name`                  | ✅   | string  | 工具名                                |
| `tool.status`                | ✅   | string  | `"success"` / `"blocked"` / `"error"` |
| `tool.readonly`              | ✅   | boolean | 始终 `true`                           |
| `summary`                    | ✅   | string  | 人类可读摘要                          |
| `items`                      | ✅   | array   | 结构化 items 列表                     |
| `safety.raw_result_returned` | ✅   | boolean | 始终 `false`                          |
| `safety.write_operation`     | ✅   | boolean | 始终 `false`                          |
| `safety.permission_filtered` | ✅   | boolean | 始终 `true`                           |

---

## 3. mcp_result 是否已移除

**是。** endpoint 返回 `mcp_preview` 而非 `mcp_result`。`build_mcp_preview()` 从内部 `mcp_result` 构建安全结构，原始 `mcp_result` 不返回前端。

---

## 4. standard prompt-response 是否保持兼容

**是。** `mode=standard` 时走原有 `get_llm_response()` 路径，返回 `response` + `response_html`，不受 MCP 改动影响。

---

## 5. 前端 Tool Preview 检查结果

| 检查项                                            | 结果 |
| ------------------------------------------------- | ---- |
| MCP mode 只在 `enable_ai_mcp_runtime=true` 时显示 | ✅   |
| 默认 Standard Chat                                | ✅   |
| `extractMCPPreview()` 只读 `mcp_preview`          | ✅   |
| `extractAIResponse()` 不读 `mcp_preview`          | ✅   |
| Tool Preview 显示工具名                           | ✅   |
| Tool Preview 显示状态标签                         | ✅   |
| Tool Preview 显示 adapter 标签                    | ✅   |
| Tool Preview 显示 summary                         | ✅   |
| Tool Preview 显示 items 列表                      | ✅   |
| Tool Preview 显示安全提示                         | ✅   |
| 使用 `metadata.id` 作为 key，非数组 index         | ✅   |

---

## 6. raw JSON 是否仍可能展示

**否。** `mcp_result` 已从响应中移除。`extractAIResponse()` 不读 `mcp_preview`。`mcp_preview` 只包含结构化安全字段。

---

## 7. secret 是否仍可能展示

**否。** `build_mcp_preview()` 只提取安全字段（id, name, identifier, description, display_name, email, state, priority, color, start_date, end_date）。不包含 token、API key、cookie、password、stack trace、env。

---

## 8. metadata 字段白名单检查

| 工具             | metadata 字段 |
| ---------------- | ------------- |
| get_me           | `id`          |
| list_projects    | `id`          |
| retrieve_project | `id`          |
| list_work_items  | `id`          |
| list_states      | `id`, `color` |
| list_labels      | `id`, `color` |
| list_cycles      | `id`          |
| list_modules     | `id`          |

所有 metadata 只包含标识字段，无敏感数据。

---

## 9. mock adapter 检查

| 检查项                                | 结果 |
| ------------------------------------- | ---- |
| 默认启用                              | ✅   |
| 使用 Phase 6.6 权限加固               | ✅   |
| 结果通过 `build_mcp_preview()` 结构化 | ✅   |
| 不返回 raw result                     | ✅   |

---

## 10. stdio adapter 检查

| 检查项                                                 | 结果 |
| ------------------------------------------------------ | ---- |
| 仅 `AI_MCP_ADAPTER=stdio` 时启用                       | ✅   |
| 不自动 fallback                                        | ✅   |
| allowed tools: get_me, list_projects, retrieve_project | ✅   |
| blocked tools: 其他 7 个                               | ✅   |
| 结果经过 `_filter_stdio_result()` 后置过滤             | ✅   |
| 结果通过 `build_mcp_preview()` 结构化                  | ✅   |

---

## 11. blocked tools 检查

stdio blocked tools 返回：

- `tool.status = "blocked"`
- `summary = "This tool is not available via MCP stdio adapter..."`
- `items = []`

前端以黄色标签展示 "blocked" 状态。

---

## 12. 写操作硬拒绝检查

| 检查项                       | 结果 |
| ---------------------------- | ---- |
| `READ_ONLY_TOOLS` 白名单     | ✅   |
| `PROHIBITED_PATTERNS` 列表   | ✅   |
| `is_tool_allowed()` 双重检查 | ✅   |
| stdio adapter 入口检查       | ✅   |
| 安全闸门检查                 | ✅   |

---

## 13. 是否做了小修复

**否。** 验证通过，无需修复。

---

## 14. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/mcp_stdio_adapter.py`    | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 15. typecheck/lint 结果

| 检查      | 结果    | 备注                   |
| --------- | ------- | ---------------------- |
| typecheck | ✅ 通过 | exit 0                 |
| lint      | ✅ 通过 | 0 errors, 997 warnings |

---

## 16. 是否新增 migration

**否。**

---

## 17. 是否修改 Docker

**否。**

---

## 18. 是否实现写操作

**否。**

---

## 19. 是否可以进入 Phase 8 audit logging

**是。** API contract 稳定，安全验证通过。

---

## 20. 是否可以进入写操作阶段

**否。** 建议先完成 audit logging，再考虑写操作。
