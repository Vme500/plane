# 第 9.3.7F 阶段报告：Isolated Dev Test Data

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：测试数据创建完成，完整性验证通过

---

## 1. 当前分支和 commit

| 项目        | 值                                                             |
| ----------- | -------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                         |
| 最新 commit | `b8d6a98f0d` — `docs: verify isolated AI dev stack migrations` |
| 工作区状态  | 有未提交 docs 报告                                             |

---

## 2. Dev stack 隔离性确认

| 检查项               | 结果              |
| -------------------- | ----------------- |
| compose project name | `plane-ai-dev` ✅ |
| API 端口             | 18180 ✅          |
| Web 端口             | 18181 ✅          |
| 不占用 18080         | ✅                |
| 独立 volume          | ✅                |

---

## 3. Fork AI 代码存在性确认

✅ 容器内 `/code/plane/ai/mcp_runtime.py` 包含 `confirmation_token`、`update_work_item_state`、`_generate_proposed_action`。

---

## 4. 测试数据创建方式

**Django shell**（方案 C）。在 isolated dev DB 中直接创建。

---

## 5. 测试数据

| 项目                | 值                                     |
| ------------------- | -------------------------------------- |
| workspace_slug      | `ai-test`                              |
| workspace_id        | `fa4377dd-0118-438f-bca8-9b4ce852c63b` |
| project_id          | `d8df8419-6bde-433e-8b31-1012d19deed3` |
| project_identifier  | `AITEST`                               |
| issue_id            | `7c63e4ec-6311-495d-b5b9-07de2ef2a21e` |
| issue_name          | `AI State Update Runtime Test`         |
| current_state_id    | `32b385fc-5a51-4b14-ac01-3d9ffa8e9fd3` |
| current_state_name  | `Todo`                                 |
| target_state_id     | `42fa6103-d432-4596-9c7e-d5e8bb238f54` |
| target_state_name   | `In Progress`                          |
| rollback_state_id   | `32b385fc-5a51-4b14-ac01-3d9ffa8e9fd3` |
| rollback_state_name | `Todo`                                 |

---

## 6. 测试用户角色

| 项目           | 值                                     |
| -------------- | -------------------------------------- |
| user_id        | `f6bf5655-b3e7-44c0-a3a2-7972bbde2710` |
| email          | `admin@ai-test.local`                  |
| workspace role | ADMIN (20)                             |
| project role   | ADMIN (20)                             |

---

## 7. 数据完整性验证

| 检查项                              | 结果 |
| ----------------------------------- | ---- |
| issue 存在                          | ✅   |
| issue 属于 workspace                | ✅   |
| issue 属于 project                  | ✅   |
| current state 属于 project          | ✅   |
| target state 属于 project           | ✅   |
| current_state_id != target_state_id | ✅   |
| user 是 workspace member            | ✅   |
| user 是 project ADMIN               | ✅   |

---

## 8. 是否执行 proposed_action

**否。**

---

## 9. 是否执行 Confirm

**否。**

---

## 10. 是否发送 confirm_action_id

**否。**

---

## 11. 是否调用 stdio write

**否。**

---

## 12. 是否调用 plane-mcp-server write

**否。**

---

## 13. 是否修改 isolated dev DB

**是。** 只创建测试数据（workspace, project, states, issue, user）。

---

## 14. 是否影响 18080 官方环境

**否。**

---

## 15. 是否修改生产目录

**否。**

---

## 16. 是否输出 secret

**否。**

---

## 17. Phase 9.3.8 输入

| 参数              | 值                                     |
| ----------------- | -------------------------------------- |
| workspace_slug    | `ai-test`                              |
| issue_id          | `7c63e4ec-6311-495d-b5b9-07de2ef2a21e` |
| target_state_id   | `42fa6103-d432-4596-9c7e-d5e8bb238f54` |
| rollback_state_id | `32b385fc-5a51-4b14-ac01-3d9ffa8e9fd3` |
| test_user_role    | ADMIN (20)                             |
| API URL           | `http://localhost:18180`               |
| Web URL           | `http://localhost:18181`               |

---

## 18. 是否可以进入 Phase 9.3.8

**是。** 测试数据已就绪，可执行 runtime test。

---

## 19. Phase 9.3.8A 验证记录（2026-06-02）

Phase 9.3.8A 验证了 proposed_action 运行时生成，详见 [`PHASE_9_3_8A_PROPOSED_ACTION_RUNTIME_REPORT.md`](./PHASE_9_3_8A_PROPOSED_ACTION_RUNTIME_REPORT.md)。

**结果**：

- ✅ proposed_action 生成成功
- ✅ execution_enabled=True
- ✅ Issue state 未变（仍为 Todo）
