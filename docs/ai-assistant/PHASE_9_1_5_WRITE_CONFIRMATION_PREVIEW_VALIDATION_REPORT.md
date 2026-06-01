# 第 9.1.5 阶段报告：AI Write Confirmation Preview Safety Validation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：验证完成，无需修复

---

## 1. 当前分支和 commit

| 项目        | 值                                                       |
| ----------- | -------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                   |
| 最新 commit | `02ebbd2068` — `feat: add AI write confirmation preview` |
| 工作区状态  | 干净（无未提交修改）                                     |

---

## 2. 后端 proposed_action 检查结果

| 检查项                                      | 结果 |
| ------------------------------------------- | ---- |
| `_generate_proposed_action()` 不执行写操作  | ✅   |
| `build_mcp_preview()` 只生成 preview        | ✅   |
| `execution_enabled` 始终 false              | ✅   |
| `requires_confirmation` 始终 true           | ✅   |
| `action_type` 只允许 update_work_item_state | ✅   |
| `target_type` 只允许 work_item              | ✅   |
| `risk_level` 只允许 low/medium/high         | ✅   |
| `expires_at` 正确设置（now + 5min）         | ✅   |
| 不包含 raw prompt                           | ✅   |
| 不包含 raw LLM result                       | ✅   |
| 不包含 raw MCP result                       | ✅   |
| 不包含 token/API key/cookie/password        | ✅   |
| 不包含 headers/stack/env                    | ✅   |
| 不包含 full work item object                | ✅   |
| 不包含 full user object                     | ✅   |
| 没有调用 save/update/delete/archive/bulk    | ✅   |
| 没有调用 Plane write service                | ✅   |
| 没有调用 stdio write                        | ✅   |
| 没有调用 plane-mcp-server write             | ✅   |

---

## 3. confirm_action_id 检查结果

| 检查项                            | 结果 |
| --------------------------------- | ---- |
| 不执行真实写操作                  | ✅   |
| 返回 execution_not_enabled        | ✅   |
| 记录 ai.write.rejected            | ✅   |
| 不调用 update_work_item_state     | ✅   |
| 不调用 issue/work item/state save | ✅   |
| 不调用 stdio adapter              | ✅   |
| 不调用 plane-mcp-server           | ✅   |
| 不修改任何业务数据                | ✅   |
| response contract 向后兼容        | ✅   |
| 不恢复 mcp_result                 | ✅   |

---

## 4. API contract 检查结果

| 检查项                                 | 结果 |
| -------------------------------------- | ---- |
| mcp_preview contract 保持兼容          | ✅   |
| proposed_action 是可选字段             | ✅   |
| proposed_action 缺失时前端不报错       | ✅   |
| standard mode 不受影响                 | ✅   |
| existing prompt-response 不受影响      | ✅   |
| existing MCP preview UI 不受影响       | ✅   |
| mcp_result 没有恢复                    | ✅   |
| proposed_action 不返回 raw JSON 大对象 | ✅   |
| proposed_action 字段与前端类型一致     | ✅   |

---

## 5. 前端 confirmation card 检查结果

| 检查项                                | 结果 |
| ------------------------------------- | ---- |
| 只展示安全字段                        | ✅   |
| 不展示 raw prompt                     | ✅   |
| 不展示 raw result                     | ✅   |
| 不展示 raw MCP result                 | ✅   |
| 不展示 secret                         | ✅   |
| 不展示 raw JSON                       | ✅   |
| Confirm 按钮 disabled                 | ✅   |
| Confirm 点击不会发送执行请求          | ✅   |
| Cancel 不执行写操作                   | ✅   |
| execution_enabled=false 时文案明确    | ✅   |
| 不误导用户以为已经执行                | ✅   |
| 不破坏现有 chat 输入和 MCP preview UI | ✅   |
| 不新增前端依赖                        | ✅   |
| 不修改 lockfile                       | ✅   |

---

## 6. audit logging 检查结果

| 检查项                                           | 结果 |
| ------------------------------------------------ | ---- |
| 生成 proposed_action 时记录 ai.write.proposed    | ✅   |
| confirm_action_id 被拒绝时记录 ai.write.rejected | ✅   |
| write_operation=true                             | ✅   |
| readonly=false                                   | ✅   |
| raw_result_returned=false                        | ✅   |
| error_code=execution_not_enabled 用于 rejected   | ✅   |
| 不记录 raw prompt                                | ✅   |
| 不记录 raw result                                | ✅   |
| 不记录 raw MCP result                            | ✅   |
| 不记录 token/API key/cookie/password             | ✅   |
| 不记录 headers/stack/env                         | ✅   |
| 不记录 full work item/state/user object          | ✅   |

---

## 7. grep 真实写操作检查结果

| 检查                    | 命中                                            | 安全性                            |
| ----------------------- | ----------------------------------------------- | --------------------------------- |
| `.save/.update/.delete` | `client.chat.completions.create()` (OpenAI API) | ✅ 安全（非 DB 写）               |
| `mcp_result`            | 内部变量名                                      | ✅ 安全（不返回前端 raw）         |
| `raw_result`            | 内部变量名                                      | ✅ 安全（权限过滤用）             |
| `token/api_key`         | docstrings, LLM config                          | ✅ 安全（不传入 proposed_action） |

---

## 8. execution_enabled 是否始终 false

**是。**

---

## 9. Confirm 是否 disabled/no-op

**是。** 前端 Confirm 按钮 disabled，后端 confirm_action_id 返回 execution_not_enabled。

---

## 10. 是否执行真实写操作

**否。**

---

## 11. 是否调用 stdio write

**否。**

---

## 12. 是否调用 plane-mcp-server write

**否。**

---

## 13. 是否修改 work item/issue/state/project

**否。**

---

## 14. 是否返回 raw prompt/result/MCP result

**否。**

---

## 15. 是否返回 token/API key/cookie/password

**否。**

---

## 16. 是否新增 migration

**否。**

---

## 17. 是否修改 Docker

**否。**

---

## 18. 是否做了小修复

**否。** 验证通过，无需修复。

---

## 19. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`         | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 20. 前端 typecheck/lint 结果

| 检查      | 结果                |
| --------- | ------------------- |
| typecheck | ✅ 通过             |
| lint      | ✅ 通过（0 errors） |

---

## 21. 是否可以 push

**是。**

---

## 22. 是否可以进入 Phase 9.2

**是。** 所有安全验证通过，可实现 target 解析 + 真实写操作（走 Plane 内部权限校验）。

---

## 23. Phase 9.2 设计记录（2026-05-28）

Phase 9.2 设计了 confirmed update_work_item_state 实现方案，详见 [`PHASE_9_2_CONFIRMED_STATE_UPDATE_DESIGN.md`](./PHASE_9_2_CONFIRMED_STATE_UPDATE_DESIGN.md)。

**设计结论**：

- signed payload 确认 token（不落库）
- 直接 ORM 更新 + activity dispatch
- 权限：workspace member + project member (ADMIN/MEMBER)
- 不需要新增 migration
