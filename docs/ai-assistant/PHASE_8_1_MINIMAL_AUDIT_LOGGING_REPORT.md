# 第 8.1 阶段报告：Minimal Safe AI/MCP Audit Logging

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                   |
| ---------- | ---------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`               |
| 基于       | `e3b7e242de` — `docs: research AI MCP audit logging` |
| 工作区状态 | 干净（无未提交修改）                                 |

---

## 2. 修改文件清单

| 文件                                        | 变更                              |
| ------------------------------------------- | --------------------------------- |
| `apps/api/plane/ai/audit_logger.py`         | 新增：审计日志 helper 模块        |
| `apps/api/plane/ai/mcp_runtime.py`          | 修改：添加 tool-level 审计事件    |
| `apps/api/plane/app/views/external/base.py` | 修改：添加 request-level 审计事件 |

---

## 3. audit logger 文件路径

`apps/api/plane/ai/audit_logger.py`

---

## 4. logger name

`plane.ai.audit`

---

## 5. 记录了哪些事件

| 事件                 | 记录位置    | 触发条件                                                                |
| -------------------- | ----------- | ----------------------------------------------------------------------- |
| `ai.request`         | endpoint    | 每次 AI 请求（standard/mcp）                                            |
| `ai.request.success` | endpoint    | standard mode 成功                                                      |
| `ai.request.error`   | endpoint    | standard mode LLM 错误                                                  |
| `ai.tool.call`       | endpoint    | MCP tool 成功                                                           |
| `ai.tool.error`      | endpoint    | MCP tool 失败                                                           |
| `ai.tool.blocked`    | mcp_runtime | MCP runtime disabled / 未识别工具 / stdio blocked / unsupported adapter |
| `ai.tool.rejected`   | mcp_runtime | 写操作被拒绝                                                            |

---

## 6. 每类事件记录哪些字段

### ai.request

| 字段                | 值                      |
| ------------------- | ----------------------- |
| event               | `ai.request`            |
| timestamp           | ISO 8601                |
| workspace_slug      | 当前 workspace          |
| user_id             | 当前 user UUID          |
| mode                | `standard` / `mcp`      |
| prompt_length       | prompt 字符数（非内容） |
| readonly            | `true`                  |
| raw_result_returned | `false`                 |
| write_operation     | `false`                 |
| source              | `pi-chat`               |

### ai.tool.call / ai.tool.error

| 字段                | 值                               |
| ------------------- | -------------------------------- |
| event               | `ai.tool.call` / `ai.tool.error` |
| timestamp           | ISO 8601                         |
| workspace_slug      | 当前 workspace                   |
| user_id             | 当前 user UUID                   |
| mode                | `mcp`                            |
| adapter             | `mock` / `stdio`                 |
| tool_name           | MCP 工具名                       |
| tool_status         | `success` / `blocked` / `error`  |
| permission_filtered | `true` / `false`                 |
| item_count          | 返回 item 数量                   |
| duration_ms         | 请求耗时                         |
| error_code          | 安全错误码（失败时）             |
| readonly            | `true`                           |
| raw_result_returned | `false`                          |
| write_operation     | `false`                          |

### ai.tool.blocked / ai.tool.rejected

| 字段            | 值                                     |
| --------------- | -------------------------------------- |
| event           | `ai.tool.blocked` / `ai.tool.rejected` |
| workspace_slug  | 当前 workspace                         |
| user_id         | 当前 user UUID                         |
| mode            | `mcp`                                  |
| adapter         | `mock` / `stdio` / 未知                |
| tool_name       | 工具名（如有）                         |
| tool_status     | `blocked` / `rejected`                 |
| write_operation | `true`（写操作被拒绝时）               |
| error_code      | 安全错误码                             |

---

## 7. 明确禁止记录哪些字段

| 字段                       | 原因             |
| -------------------------- | ---------------- |
| raw prompt 全文            | 隐私             |
| raw LLM response 全文      | 隐私             |
| raw MCP result             | 可能含敏感数据   |
| API key                    | secret           |
| token                      | secret           |
| cookie                     | secret           |
| password                   | secret           |
| request headers            | 可能含 auth 信息 |
| stack trace                | 安全             |
| env                        | 安全             |
| API key owner raw identity | 隐私             |
| full model object          | 安全             |
| full user object           | 隐私             |
| raw exception message      | 可能含敏感信息   |

---

## 8. 是否记录 raw prompt

**否。** 只记录 `prompt_length`（字符数）。

---

## 9. 是否记录 raw result

**否。** 只记录 `item_count`。

---

## 10. 是否记录 secret

**否。** 字段白名单中无 secret 字段。

---

## 11. 是否改变 API contract

**否。** standard mode 和 mcp_preview 响应结构不变。

---

## 12. 是否新增 migration

**否。**

---

## 13. 是否修改 Docker

**否。**

---

## 14. 是否实现写操作

**否。** 写操作仍硬拒绝，并记录 `ai.tool.rejected`。

---

## 15. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/audit_logger.py`         | ✅ 通过 |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/mcp_stdio_adapter.py`    | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 16. 是否改前端

**否。**

---

## 17. 已知问题

| 问题                     | 说明                                       |
| ------------------------ | ------------------------------------------ |
| 日志输出到 stdout/stderr | 需要运维工具（ELK/Datadog/CloudWatch）收集 |
| 无持久化                 | 日志不写入数据库，重启后丢失               |
| 无 API 查询              | 不能通过 API 查询审计日志                  |
| 无前端 UI                | 无 admin 审计日志查看页面                  |

---

## 18. Phase 8.2 / Phase 9 建议

- Phase 8.2：数据库持久化（AIAuditEvent model + migration）
- Phase 8.3：admin-only audit log API endpoint
- Phase 8.4：admin-only audit log 前端页面
- Phase 9：写操作确认机制

---

## error_code 规范

| error_code                 | 说明                        |
| -------------------------- | --------------------------- |
| `invalid_mode`             | 无效的 mode 参数            |
| `mcp_runtime_disabled`     | ENABLE_AI_MCP_RUNTIME=false |
| `unsupported_adapter`      | AI_MCP_ADAPTER 值无效       |
| `tool_not_allowed`         | 工具不在白名单或被禁止      |
| `write_operation_rejected` | 写操作被拒绝                |
| `stdio_timeout`            | stdio adapter 超时          |
| `stdio_start_failed`       | stdio subprocess 启动失败   |
| `stdio_permission_gate`    | stdio 权限闸门拒绝          |
| `stdio_result_blocked`     | stdio 工具被安全闸门阻断    |
| `mcp_tool_error`           | MCP 工具执行错误            |
| `llm_request_error`        | LLM 请求错误                |
| `unknown_error`            | 未知错误                    |

---

## 19. Phase 8.2 验证记录（2026-05-28）

Phase 8.2 验证了 audit logging 安全性，详见 [`PHASE_8_2_AUDIT_LOGGING_VALIDATION_REPORT.md`](./PHASE_8_2_AUDIT_LOGGING_VALIDATION_REPORT.md)。

**验证结果**：

- ✅ 不记录 raw prompt / raw result / raw MCP result
- ✅ 不记录 secret / headers / stack trace / env
- ✅ grep 敏感字段检查通过
- ✅ API contract 未改变
- ✅ 无需代码修复
