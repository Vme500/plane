# 第 9.3.5 阶段报告：Confirmed update_work_item_state Security Validation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：验证完成，无需修复

---

## 1. 当前分支和 commit

| 项目        | 值                                                        |
| ----------- | --------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                    |
| 最新 commit | `f4123cca80` — `feat: confirm AI work item state updates` |
| 工作区状态  | 干净（无未提交修改）                                      |

---

## 2. 写入路径验证结果

| 检查项                          | 结果                                          |
| ------------------------------- | --------------------------------------------- |
| 写入方式                        | `issue.state_id = new_state_id; issue.save()` |
| 是否绕过 `_sync_completed_at()` | ✅ 不绕过（`issue.save()` 触发）              |
| 是否绕过 `ChangeTrackerMixin`   | ✅ 不绕过（`issue.save()` 触发）              |
| activity dispatch               | ✅ 手动派发 `issue_activity.delay()`          |
| 是否绕过 serializer 校验        | ⚠️ 绕过 IssueSerializer，但校验在执行前完成   |
| 是否绕过 project/workspace 约束 | ✅ 不绕过（权限校验在执行前完成）             |

### 为什么直接 ORM 是安全的

1. **权限校验在执行前完成**：workspace member + project member (ADMIN/MEMBER) + issue 属于 workspace/project
2. **state 校验在执行前完成**：proposed state 属于同一 project
3. **current_state 一致性检查**：防止并发修改
4. **`issue.save()` 触发所有 model-level side effects**：`_sync_completed_at()`, `ChangeTrackerMixin`
5. **activity dispatch 手动完成**：与现有 update endpoint 等价
6. **只更新 state_id**：不更新其他字段

---

## 3. 权限链验证结果

| 检查项                            | 结果                             |
| --------------------------------- | -------------------------------- |
| request.user 已认证               | ✅（`@allow_permission` 装饰器） |
| token actor_id == request.user.id | ✅（line 376）                   |
| token workspace_slug == URL slug  | ✅（line 380）                   |
| user 是 workspace member          | ✅（line 395）                   |
| user 是 project member            | ✅（line 402）                   |
| role 是 ADMIN 或 MEMBER           | ✅（`role__in=[20, 15]`）        |
| GUEST 禁止                        | ✅                               |
| 非 workspace member 禁止          | ✅                               |
| project 外成员禁止                | ✅                               |
| issue 属于 URL workspace          | ✅（`workspace__slug=slug`）     |
| proposed state 属于同一 project   | ✅（line 410）                   |
| current_state_id 一致性           | ✅（line 418）                   |
| 不允许跨 workspace target         | ✅                               |
| 不允许跨 project state            | ✅                               |

---

## 4. signed token 验证结果

| 检查项                                     | 结果           |
| ------------------------------------------ | -------------- |
| 使用 TimestampSigner                       | ✅             |
| max_age=300 秒                             | ✅             |
| payload 包含必要字段                       | ✅             |
| confirm_action_id 校验                     | ✅（line 384） |
| token 无效返回 confirmation_token_invalid  | ✅             |
| token 过期返回 confirmation_token_expired  | ✅             |
| actor mismatch 返回 action_actor_mismatch  | ✅             |
| workspace mismatch 返回 workspace_mismatch | ✅             |
| token 不写入 audit log                     | ✅             |
| token 不展示在 UI                          | ✅             |
| token 不输出到 server log                  | ✅             |

---

## 5. proposed_action 生成条件验证结果

| 检查项                                             | 结果 |
| -------------------------------------------------- | ---- |
| issue_id 是 UUID                                   | ✅   |
| proposed_state_id 是 UUID                          | ✅   |
| issue 存在                                         | ✅   |
| issue 属于当前 workspace                           | ✅   |
| state 属于同一 project                             | ✅   |
| user 是 workspace member                           | ✅   |
| user 是 project member ADMIN/MEMBER                | ✅   |
| current_state_id 从 DB 读取                        | ✅   |
| 不支持 identifier                                  | ✅   |
| 不支持模糊标题                                     | ✅   |
| 不支持 state name 模糊匹配                         | ✅   |
| 不支持 bulk                                        | ✅   |
| 不支持 delete/archive/create/assign/label/priority | ✅   |

---

## 6. confirm 执行范围验证结果

| 检查项                        | 结果 |
| ----------------------------- | ---- |
| 只允许 update_work_item_state | ✅   |
| 只更新 Issue.state            | ✅   |
| 不更新 title                  | ✅   |
| 不更新 description            | ✅   |
| 不更新 assignee               | ✅   |
| 不更新 label                  | ✅   |
| 不更新 priority               | ✅   |
| 不更新 cycle/module           | ✅   |
| 不更新 project                | ✅   |
| 不更新 archived_at/deleted_at | ✅   |
| 不允许 bulk                   | ✅   |
| 不允许 create/delete          | ✅   |

---

## 7. stdio/plane-mcp-server 禁止写验证结果

| 检查项                           | 结果 |
| -------------------------------- | ---- |
| confirm 不调用 stdio adapter     | ✅   |
| confirm 不调用 plane-mcp-server  | ✅   |
| confirm 不使用 workspace API key | ✅   |
| 所有权限来自 request.user        | ✅   |
| 所有数据写入走 Plane 内部路径    | ✅   |

---

## 8. audit events 验证结果

| 检查项                               | 结果 |
| ------------------------------------ | ---- |
| ai.write.proposed                    | ✅   |
| ai.write.confirmed                   | ✅   |
| ai.write.executed                    | ✅   |
| ai.write.rejected                    | ✅   |
| ai.write.error                       | ✅   |
| 不记录 confirmation_token            | ✅   |
| 不记录 raw prompt/result/MCP result  | ✅   |
| 不记录 full issue/state object       | ✅   |
| 不记录 token/API key/cookie/password | ✅   |
| 不记录 headers/stack/env             | ✅   |
| error 只记录安全 error_code          | ✅   |
| executed item_count=1                | ✅   |
| write_operation=true                 | ✅   |
| readonly=false                       | ✅   |

---

## 9. 前端 Confirm 验证结果

| 检查项                                      | 结果 |
| ------------------------------------------- | ---- |
| execution_enabled=true + token 存在时可点击 | ✅   |
| 发送 confirm_action_id + confirmation_token | ✅   |
| 不展示 confirmation_token                   | ✅   |
| 不展示 raw JSON                             | ✅   |
| 不展示 secret                               | ✅   |
| success 显示安全 summary                    | ✅   |
| failure 显示安全 error                      | ✅   |
| 不做 optimistic update                      | ✅   |
| 不自动重试                                  | ✅   |
| execution_enabled=false 时 disabled         | ✅   |
| 不修改 lockfile                             | ✅   |
| 不新增依赖                                  | ✅   |

---

## 10. grep 检查结果

| 检查                     | 命中                                                             | 安全性                       |
| ------------------------ | ---------------------------------------------------------------- | ---------------------------- |
| `.save()`                | `issue.save()` (intentional), `client.chat.completions.create()` | ✅ 安全                      |
| `stdio/plane-mcp-server` | docstrings, stdio adapter code                                   | ✅ 安全（不在 confirm path） |
| `mcp_result`             | 内部变量名                                                       | ✅ 安全                      |
| `api_key`                | LLM config reading                                               | ✅ 安全（不在 confirm path） |

---

## 11. 是否只更新 state

**是。**

---

## 12. 是否执行真实确认请求

**否。**

---

## 13. 是否修改 work item/issue/state/project 数据

**否。**

---

## 14. 是否做了小修复

**否。** 验证通过，无需修复。

---

## 15. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`         | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 16. 前端 typecheck/lint 结果

Phase 9.3 已验证通过（typecheck exit 0, lint 0 errors）。Phase 9.3.5 未修改前端代码。

---

## 17. 是否新增 migration

**否。**

---

## 18. 是否修改 Docker

**否。**

---

## 19. 是否可以 push

**是。**

---

## 20. 是否可以进入真实环境手动测试阶段

**是。** 所有安全验证通过，可在完整 Django 环境中进行手动确认流程测试。

---

## 21. Phase 9.3.6 测试计划记录（2026-05-28）

Phase 9.3.6 设计了 runtime test plan，详见 [`PHASE_9_3_6_CONFIRMED_STATE_UPDATE_RUNTIME_TEST_PLAN.md`](./PHASE_9_3_6_CONFIRMED_STATE_UPDATE_RUNTIME_TEST_PLAN.md)。

**测试计划**：

- 4 个成功路径 + 12 个拒绝路径测试用例
- 9 个安全检查项
- 回滚方案 + step-by-step 命令
