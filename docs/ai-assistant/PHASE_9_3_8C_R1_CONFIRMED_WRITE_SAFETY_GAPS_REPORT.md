# 第 9.3.8C-R1 阶段报告：Confirmed Write Safety Gaps

> 日期：2026-06-03
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：安全检查完成

---

## 1. Issue 当前状态

| 项目              | 值             |
| ----------------- | -------------- |
| state             | In Progress ✅ |
| state_id          | `42fa6103-...` |
| ai.write.executed | 1 ✅           |

---

## 2. Audit 脱敏字段检查

| 字段                | 值                     | 安全 |
| ------------------- | ---------------------- | ---- |
| event               | ai.write.executed      | ✅   |
| tool_name           | update_work_item_state | ✅   |
| tool_status         | executed               | ✅   |
| raw_result_returned | false                  | ✅   |
| item_count          | 1                      | ✅   |
| error_code          | None                   | ✅   |
| confirmation_token  | 未记录                 | ✅   |
| raw prompt          | 未记录                 | ✅   |
| raw result          | 未记录                 | ✅   |

---

## 3. Replay Protection 检查

**代码级检查结果：**

| 防护机制           | 实现                                            |
| ------------------ | ----------------------------------------------- |
| Token 过期         | `TimestampSigner(max_age=300)` — 5 分钟过期 ✅  |
| Actor 绑定         | `payload.actor_id == request.user.id` ✅        |
| Workspace 绑定     | `payload.workspace_slug == URL slug` ✅         |
| Action ID 匹配     | `payload.action_id == confirm_action_id` ✅     |
| Current state 校验 | `issue.state_id == payload.current_state_id` ✅ |
| 幂等性             | 设置相同 state 结果相同 ✅                      |

**结论**：Replay protection 通过 `current_state_id` 校验实现。重复执行同一 token 时，如果 state 已变化，会被拒绝。如果 state 未变化，设置相同 state 是幂等的。

---

## 4. Permission / Target Validation 检查

| 检查项                        | 实现                                                |
| ----------------------------- | --------------------------------------------------- |
| Workspace member              | ✅ `WorkspaceMember.objects.filter(...)`            |
| Project member (ADMIN/MEMBER) | ✅ `ProjectMember.objects.filter(role__in=[20,15])` |
| Issue exists                  | ✅ `Issue.objects.get(pk=issue_id)`                 |
| Issue belongs to workspace    | ✅ `workspace__slug=slug`                           |
| Issue belongs to project      | ✅ `issue.project_id == project_id`                 |
| State belongs to project      | ✅ `State.objects.get(pk=..., project_id=...)`      |
| Action type allowlist         | ✅ 只允许 `update_work_item_state`                  |
| Cross-workspace blocked       | ✅                                                  |

---

## 5. UI 安全检查

| 检查项                                                    | 结果 |
| --------------------------------------------------------- | ---- |
| confirmation_token 值不显示                               | ✅   |
| 只显示 token=true 布尔值                                  | ✅   |
| Confirm 依赖 canConfirm                                   | ✅   |
| disabled = !canConfirm                                    | ✅   |
| canConfirm = executionEnabled && confirmationTokenPresent | ✅   |
| 不显示 raw JSON                                           | ✅   |
| 不显示 raw MCP result                                     | ✅   |
| 错误消息不泄露 secret                                     | ✅   |

---

## 6. 诊断行建议

`req/exec/token/can_confirm` 诊断行应：

- **短期保留**：方便调试
- **后续隐藏**：仅在 dev flag 下显示
- **生产环境不显示**

---

## 7. 安全总结

| 检查项                   | 结果                                  |
| ------------------------ | ------------------------------------- |
| token 泄露               | 否 ✅                                 |
| raw prompt 泄露          | 否 ✅                                 |
| raw result 泄露          | 否 ✅                                 |
| replay protection        | 有（state_id 校验 + token expiry） ✅ |
| permission validation    | 完整 ✅                               |
| target validation        | 完整 ✅                               |
| UI 安全                  | 通过 ✅                               |
| 18080 未影响             | ✅                                    |
| ai.write.executed 仍为 1 | ✅                                    |
| issue 仍为 In Progress   | ✅                                    |
