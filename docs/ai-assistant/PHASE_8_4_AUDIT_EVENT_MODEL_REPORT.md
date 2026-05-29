# 第 8.4 阶段报告：AIAuditEvent Model + Migration + Write Helper

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                       |
| ---------- | -------------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                   |
| 基于       | `595e1464d9` — `docs: design AI audit event persistence` |
| 工作区状态 | 干净（无未提交修改）                                     |

---

## 2. 修改文件清单

| 文件                                                | 变更                                                       |
| --------------------------------------------------- | ---------------------------------------------------------- |
| `apps/api/plane/db/models/ai.py`                    | 新增：AIAuditEvent model                                   |
| `apps/api/plane/db/models/__init__.py`              | 修改：注册 AIAuditEvent                                    |
| `apps/api/plane/db/migrations/0122_aiauditevent.py` | 新增：migration                                            |
| `apps/api/plane/ai/audit_logger.py`                 | 修改：新增 `create_ai_audit_event()` helper                |
| `apps/api/plane/ai/mcp_runtime.py`                  | 修改：使用 `create_ai_audit_event()` 替代 `log_ai_event()` |
| `apps/api/plane/app/views/external/base.py`         | 修改：使用 `create_ai_audit_event()` 替代 `log_ai_event()` |

---

## 3. AIAuditEvent model 文件路径

`apps/api/plane/db/models/ai.py`

---

## 4. 字段清单

| 字段                  | 类型                 | Nullable | 说明                                                                           |
| --------------------- | -------------------- | -------- | ------------------------------------------------------------------------------ |
| `id`                  | UUIDField            | PK       | 自动继承 BaseModel                                                             |
| `workspace`           | FK(Workspace)        | 否       | 关联 workspace                                                                 |
| `actor`               | FK(User)             | 是       | 操作用户                                                                       |
| `event`               | CharField(64)        | 否       | ai.request / ai.tool.call / ai.tool.blocked / ai.tool.error / ai.tool.rejected |
| `mode`                | CharField(16)        | 是       | standard / mcp                                                                 |
| `adapter`             | CharField(16)        | 是       | none / mock / stdio                                                            |
| `tool_name`           | CharField(64)        | 是       | MCP 工具名                                                                     |
| `tool_status`         | CharField(16)        | 是       | success / blocked / error / rejected                                           |
| `readonly`            | BooleanField         | 否       | 始终 True                                                                      |
| `permission_filtered` | BooleanField         | 是       | 是否经过权限过滤                                                               |
| `raw_result_returned` | BooleanField         | 否       | 始终 False                                                                     |
| `write_operation`     | BooleanField         | 否       | 写操作标记                                                                     |
| `duration_ms`         | PositiveIntegerField | 是       | 请求耗时                                                                       |
| `item_count`          | PositiveIntegerField | 是       | 返回 item 数量                                                                 |
| `prompt_length`       | PositiveIntegerField | 是       | prompt 字符数                                                                  |
| `error_code`          | CharField(64)        | 是       | 安全错误码                                                                     |
| `source`              | CharField(32)        | 否       | pi-chat                                                                        |
| `request_id`          | CharField(64)        | 是       | 请求追踪 ID                                                                    |
| `created_at`          | DateTimeField        | 自动     | 继承自 BaseModel                                                               |
| `updated_at`          | DateTimeField        | 自动     | 继承自 BaseModel                                                               |
| `deleted_at`          | DateTimeField        | 是       | 继承自 BaseModel                                                               |
| `created_by`          | FK(User)             | 是       | 继承自 BaseModel                                                               |
| `updated_by`          | FK(User)             | 是       | 继承自 BaseModel                                                               |

---

## 5. 禁止记录字段

| 字段                                | 原因   |
| ----------------------------------- | ------ |
| raw prompt                          | 隐私   |
| raw result                          | 隐私   |
| raw MCP result                      | 安全   |
| API key / token / cookie / password | secret |
| request headers                     | 安全   |
| stack trace / env                   | 安全   |
| full request/response body          | 安全   |
| full user/model object              | 隐私   |

---

## 6. 索引

| 索引名                       | 字段                      | 用途              |
| ---------------------------- | ------------------------- | ----------------- |
| `idx_ai_audit_ws_created`    | `(workspace, created_at)` | 按 workspace 查询 |
| `idx_ai_audit_actor_created` | `(actor, created_at)`     | 按用户查询        |
| `idx_ai_audit_event_created` | `(event, created_at)`     | 按事件类型筛选    |

---

## 7. migration 文件路径

`apps/api/plane/db/migrations/0122_aiauditevent.py`

---

## 8. create_ai_audit_event helper 路径

`apps/api/plane/ai/audit_logger.py`

---

## 9. DB 写失败策略

**fail-safe**：DB 写失败只记录 `logger.warning()`，不影响 AI/MCP 主流程。

---

## 10. 是否改变 API contract

**否。**

---

## 11. 是否新增 audit API

**否。**

---

## 12. 是否新增 audit UI

**否。**

---

## 13. 是否修改 Docker

**否。**

---

## 14. 是否实现写操作

**否。** 写操作仍硬拒绝。

---

## 15. py_compile 结果

| 文件                                                | 结果    |
| --------------------------------------------------- | ------- |
| `apps/api/plane/db/models/ai.py`                    | ✅ 通过 |
| `apps/api/plane/db/migrations/0122_aiauditevent.py` | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`                 | ✅ 通过 |
| `apps/api/plane/ai/mcp_runtime.py`                  | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`                    | ✅ 通过 |
| `apps/api/plane/ai/mcp_stdio_adapter.py`            | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py`         | ✅ 通过 |

---

## 16. 是否运行 migrate

**否。** 只生成 migration 文件，不执行 `manage.py migrate`。

---

## 17. 已知问题

| 问题                       | 说明                                          |
| -------------------------- | --------------------------------------------- |
| migration 未在真实 DB 验证 | 当前环境无 Django，migration 基于现有模式手写 |
| 无读取 API                 | Phase 8.5 实现 admin-only read API            |
| 无前端 UI                  | Phase 8.6 实现                                |
| 无自动清理                 | Phase 8.5+ 实现 retention job                 |

---

## 18. Phase 8.5 建议

- admin-only read API endpoint
- Workspace Settings → AI Audit Logs 页面
- 90 天 retention 清理管理命令

---

## 19. Phase 8.4.5 验证记录（2026-05-28）

Phase 8.4.5 验证了 model/migration/persistence 安全性，详见 [`PHASE_8_4_5_AUDIT_EVENT_VALIDATION_REPORT.md`](./PHASE_8_4_5_AUDIT_EVENT_VALIDATION_REPORT.md)。

**验证结果**：

- ✅ model 字段安全，无 raw prompt/result/secret
- ✅ migration 正确
- ✅ helper fail-safe
- ✅ grep 检查通过
- ✅ 无需代码修复
