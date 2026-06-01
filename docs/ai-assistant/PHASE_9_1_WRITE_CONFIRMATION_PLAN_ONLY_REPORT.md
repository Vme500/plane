# 第 9.1 阶段报告：Write Confirmation Plan-Only Contract Implementation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile/typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                           |
| ---------- | ------------------------------------------------------------ |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                       |
| 基于       | `a60da17a64` — `docs: design AI write confirmation workflow` |
| 工作区状态 | 干净（无未提交修改）                                         |

---

## 2. 修改文件清单

| 文件                                                             | 变更                                                           |
| ---------------------------------------------------------------- | -------------------------------------------------------------- |
| `apps/api/plane/ai/mcp_runtime.py`                               | 新增 `_generate_proposed_action()`，更新 `build_mcp_preview()` |
| `apps/api/plane/app/views/external/base.py`                      | 新增 `confirm_action_id` 拦截                                  |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | 新增 `ProposedAction` 类型和 confirmation card                 |
| `docs/ai-assistant/PHASE_9_0_WRITE_CONFIRMATION_DESIGN.md`       | 修正措辞                                                       |

---

## 3. 是否修正 mock adapter 写操作措辞

**是。** 修正了 "写操作走 mock adapter 路径" → "写操作走 Plane 内部权限校验路径"。

---

## 4. proposed_action schema

| 字段                    | 类型     | 值                       |
| ----------------------- | -------- | ------------------------ |
| `action_id`             | UUID     | 自动生成                 |
| `workspace_slug`        | string   | 当前 workspace           |
| `actor_id`              | UUID     | 当前 user                |
| `action_type`           | string   | `update_work_item_state` |
| `target_type`           | string   | `work_item`              |
| `target_id`             | null     | Phase 9.1 不解析         |
| `target_display`        | null     | Phase 9.1 不解析         |
| `current_value`         | null     | Phase 9.1 不解析         |
| `proposed_value`        | null     | Phase 9.1 不解析         |
| `risk_level`            | string   | `medium`                 |
| `summary`               | string   | `Update work item state` |
| `requires_confirmation` | bool     | `true`                   |
| `expires_at`            | datetime | now + 5 分钟             |
| `execution_enabled`     | bool     | **`false`**              |

---

## 5. 是否新增 API contract 字段

**是。** mcp_preview 新增 `proposed_action` 字段（null 或 ProposedAction 对象）。

---

## 6. confirmation card 是否实现

**是。** 前端显示：

- Action type
- Target / Current / Proposed value（Phase 9.1 为 null）
- Risk level
- Expires at
- Confirm 按钮（disabled，因为 execution_enabled=false）
- Cancel 按钮

---

## 7. execution_enabled 是否为 false

**是。** Phase 9.1 所有 proposed_action 的 `execution_enabled` 始终为 `false`。

---

## 8. 是否执行真实写操作

**否。** Phase 9.1 只生成 proposed_action，不执行任何写操作。

---

## 9. confirm_action_id 行为

如果请求中带 `confirm_action_id`：

1. 记录 `ai.write.rejected` audit event
2. 返回 "execution not enabled yet" 消息
3. 不执行任何写操作

---

## 10. audit events

| event               | 触发条件                    |
| ------------------- | --------------------------- |
| `ai.write.proposed` | 生成 proposed_action 时     |
| `ai.write.rejected` | 用户带 confirm_action_id 时 |

---

## 11. 禁止字段

raw prompt, raw result, raw MCP result, token, API key, cookie, password, headers, stack trace, env, full work item object, full state object。

---

## 12. 是否调用 stdio write

**否。**

---

## 13. 是否调用 plane-mcp-server write

**否。**

---

## 14. 是否新增 migration

**否。**

---

## 15. 是否修改 Docker

**否。**

---

## 16. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`         | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 17. 前端 typecheck/lint 结果

| 检查      | 结果                |
| --------- | ------------------- |
| typecheck | ✅ 通过             |
| lint      | ✅ 通过（0 errors） |

---

## 18. grep 安全检查结果

无敏感字段命中。所有写操作相关代码只生成 proposed_action，不执行真实操作。

---

## 19. 已知限制

| 问题                                 | 说明                                 |
| ------------------------------------ | ------------------------------------ |
| target_id/target_display 为 null     | Phase 9.1 不解析自然语言中的具体目标 |
| current_value/proposed_value 为 null | Phase 9.1 不查询当前状态             |
| Confirm 按钮 disabled                | execution_enabled=false，无法执行    |

---

## 20. Phase 9.2 建议

- 实现 target 解析（从 prompt 中提取 work item 和 state）
- 实现真实 update_work_item_state（走 Plane 内部权限校验）
- 实现 execution_enabled=true 的确认执行流程
- 实现过期 token 检查
