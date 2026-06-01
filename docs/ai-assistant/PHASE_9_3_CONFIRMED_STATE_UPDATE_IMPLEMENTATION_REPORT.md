# 第 9.3 阶段报告：Confirmed update_work_item_state Implementation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile/typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                      |
| ---------- | ------------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                  |
| 基于       | `e3704f0220` — `docs: design confirmed AI state update` |
| 工作区状态 | 干净（无未提交修改）                                    |

---

## 2. 修改文件清单

| 文件                                                             | 变更                                           |
| ---------------------------------------------------------------- | ---------------------------------------------- |
| `apps/api/plane/ai/mcp_runtime.py`                               | 更新 `_generate_proposed_action()` + UUID 提取 |
| `apps/api/plane/app/views/external/base.py`                      | 新增 `_handle_write_confirmation()`            |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | 更新 Confirm 按钮 + confirmation_token         |

---

## 3. signed token 是否实现

**是。** 使用 Django `TimestampSigner`，payload 包含 action_id, workspace_slug, actor_id, issue_id, project_id, current_state_id, proposed_state_id。max_age=300 秒。

---

## 4. execution_enabled 何时为 true

当以下条件全部满足时：

1. issue_id 和 proposed_state_id 是有效 UUID
2. issue 存在且属于当前 workspace
3. user 是 workspace member
4. user 是 project member (ADMIN/MEMBER)
5. proposed state 属于同一 project

否则 execution_enabled=false（plan-only fallback）。

---

## 5. proposed_action 字段

| 字段                  | 来源                   |
| --------------------- | ---------------------- |
| action_id             | UUID 自动生成          |
| workspace_slug        | URL slug               |
| actor_id              | request.user.id        |
| action_type           | update_work_item_state |
| target_type           | work_item              |
| target_id             | issue UUID             |
| target_display        | issue.name             |
| current_value         | current state name     |
| proposed_value        | proposed state name    |
| risk_level            | medium                 |
| summary               | "Update state: X → Y"  |
| requires_confirmation | true                   |
| expires_at            | now + 5min             |
| execution_enabled     | true/false             |
| confirmation_token    | signed token           |

---

## 6. confirm request 字段

| 字段               | 说明                              |
| ------------------ | --------------------------------- |
| confirm_action_id  | action_id from proposed_action    |
| confirmation_token | signed token from proposed_action |
| mode               | "mcp"                             |
| prompt             | ""                                |
| task               | "chat"                            |

---

## 7. 权限校验是否实现

**是。** 完整校验链：

1. TimestampSigner 验签 + max_age=300
2. actor_id == request.user.id
3. workspace_slug == URL slug
4. WorkspaceMember 检查
5. Issue 存在且属于 workspace
6. ProjectMember 检查 (ADMIN/MEMBER)
7. current_state_id 一致性检查
8. proposed state 属于同一 project

---

## 8. update path 是否复用 IssueSerializer/service

**直接 ORM + activity dispatch。** 使用 `issue.state_id = new_state_id; issue.save()`，触发 `_sync_completed_at()` 和 `ChangeTrackerMixin`。手动派发 `issue_activity.delay()`。

---

## 9. 是否只更新 state

**是。** 只更新 `issue.state_id`，不更新 title/description/assignee/label/priority。

---

## 10. 是否执行真实确认请求测试

**否。** 代码已实现，但本次未执行真实确认请求。

---

## 11. 是否调用 stdio write

**否。**

---

## 12. 是否调用 plane-mcp-server write

**否。**

---

## 13. 是否新增 migration

**否。**

---

## 14. 是否修改 Docker

**否。**

---

## 15. 是否运行 migrate

**否。**

---

## 16. audit events

| event              | 触发条件                 |
| ------------------ | ------------------------ |
| ai.write.proposed  | proposed_action 生成时   |
| ai.write.confirmed | confirm_action_id 收到时 |
| ai.write.executed  | state update 成功时      |
| ai.write.rejected  | 权限/验证失败时          |
| ai.write.error     | 执行异常时               |

---

## 17. 前端 Confirm 是否实现

**是。** Confirm 按钮在 execution_enabled=true + confirmation_token 存在时可点击。点击后发送 confirm_action_id + confirmation_token。成功/失败显示对应消息。

---

## 18. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`         | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 19. 前端 typecheck/lint 结果

| 检查      | 结果                |
| --------- | ------------------- |
| typecheck | ✅ 通过             |
| lint      | ✅ 通过（0 errors） |

---

## 20. grep 安全检查结果

| 检查         | 命中                                                             | 安全性  |
| ------------ | ---------------------------------------------------------------- | ------- |
| `.save()`    | `issue.save()` (intentional), `client.chat.completions.create()` | ✅ 安全 |
| `mcp_result` | 内部变量名                                                       | ✅ 安全 |
| `raw_result` | 内部变量名                                                       | ✅ 安全 |

---

## 21. 已知限制

| 问题                      | 说明                               |
| ------------------------- | ---------------------------------- |
| 只支持 UUID               | 不支持 issue identifier 或模糊标题 |
| 只更新 state              | 不支持其他字段更新                 |
| 无 activity dispatch 容错 | Celery 不可用时 activity 不记录    |
| signed token 不落库       | 无法审计 token 使用情况            |

---

## 22. Phase 9.3.5 验证建议

- 在完整 Django 环境中测试确认流程
- 验证 signed token 过期（max_age=300）
- 验证 actor mismatch 拒绝
- 验证 current_state_mismatch 拒绝
- 验证 GUEST 被拒绝
- 验证 activity dispatch

---

## 23. Phase 9.3.5 验证记录（2026-05-28）

Phase 9.3.5 验证了 confirmed state update 安全性，详见 [`PHASE_9_3_5_CONFIRMED_STATE_UPDATE_VALIDATION_REPORT.md`](./PHASE_9_3_5_CONFIRMED_STATE_UPDATE_VALIDATION_REPORT.md)。

**验证结果**：

- ✅ 写入路径安全（`issue.save()` 触发 model-level side effects）
- ✅ 完整权限链（14 项检查）
- ✅ signed token 安全
- ✅ confirm_action_id 校验
- ✅ 只更新 state
- ✅ 无需代码修复
