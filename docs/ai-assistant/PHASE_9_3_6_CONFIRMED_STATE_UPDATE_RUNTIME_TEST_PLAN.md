# 第 9.3.6 阶段报告：Confirmed update_work_item_state Runtime Test Plan

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：测试计划完成，未执行真实测试

---

## 1. 当前分支和 commit

| 项目        | 值                                                         |
| ----------- | ---------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                     |
| 最新 commit | `8eee1dd609` — `docs: validate AI confirmed state updates` |
| 工作区状态  | 干净（无未提交修改）                                       |

---

## 2. 测试环境要求

| 要求   | 说明                                          |
| ------ | --------------------------------------------- |
| 环境   | dev/staging，**不允许在生产数据上测试**       |
| 数据库 | 已应用 AIAuditEvent migration (0122)          |
| Django | 完整运行环境（celery/psycopg/redis 可用）     |
| API    | 可访问 `/api/workspaces/<slug>/ai-assistant/` |
| 认证   | 有效 session 或 API token                     |

---

## 3. 测试数据要求

| 数据           | 说明                                   |
| -------------- | -------------------------------------- |
| 测试 workspace | slug 已知                              |
| 测试 project   | 属于测试 workspace，有至少两个 state   |
| 测试 issue     | 属于测试 project，state 已知           |
| State A        | issue 当前 state                       |
| State B        | 同一 project 的另一个 state            |
| ADMIN 用户     | workspace ADMIN + project ADMIN/MEMBER |
| MEMBER 用户    | workspace MEMBER + project MEMBER      |
| GUEST 用户     | workspace GUEST + project GUEST        |
| 无权限用户     | workspace member 但非 project member   |

---

## 4. 成功路径测试用例

### TC-01: ADMIN 生成 proposed_action

**前置**：ADMIN 用户已登录

**步骤**：

1. 发送 POST `/api/workspaces/<slug>/ai-assistant/` with `mode=mcp`, `prompt="change state <issue_id> to <state_b_id>"`
2. 检查响应

**预期**：

- `mcp_preview.tool.status = "proposed"`
- `mcp_preview.proposed_action.execution_enabled = true`
- `mcp_preview.proposed_action.confirmation_token` 存在
- `mcp_preview.proposed_action.target_id = issue_id`
- `mcp_preview.proposed_action.current_value = State A name`
- `mcp_preview.proposed_action.proposed_value = State B name`
- `mcp_preview.safety.write_operation = true`
- audit event: `ai.write.proposed`

### TC-02: ADMIN 确认执行

**前置**：TC-01 已完成，confirmation_token 已保存

**步骤**：

1. 发送 POST `/api/workspaces/<slug>/ai-assistant/` with `mode=mcp`, `confirm_action_id=<action_id>`, `confirmation_token=<token>`
2. 检查响应
3. 查询 issue 验证 state

**预期**：

- `mcp_preview.tool.status = "executed"`
- `response` 包含 "State updated: A → B"
- issue.state_id = State B id
- audit events: `ai.write.confirmed`, `ai.write.executed`
- issue activity 有记录（如 Celery 可用）

### TC-03: MEMBER 生成 proposed_action

**步骤**：同 TC-01，但使用 MEMBER 用户

**预期**：同 TC-01（MEMBER 有 project MEMBER 权限）

### TC-04: MEMBER 确认执行

**步骤**：同 TC-02，但使用 MEMBER 用户

**预期**：同 TC-02

---

## 5. 拒绝路径测试用例

### TC-05: confirmation_token 过期

**前置**：等待 > 300 秒

**步骤**：使用过期 token 发送 confirm 请求

**预期**：

- `mcp_preview.tool.status = "rejected"`
- error_code = `confirmation_token_expired`
- audit event: `ai.write.rejected`

### TC-06: confirmation_token 被篡改

**步骤**：修改 token 一个字符后发送 confirm 请求

**预期**：

- error_code = `confirmation_token_invalid`

### TC-07: confirm_action_id 与 token 不一致

**步骤**：使用随机 UUID 作为 confirm_action_id

**预期**：

- error_code = `confirmation_token_invalid`

### TC-08: actor mismatch

**步骤**：用户 A 生成 proposed_action，用户 B 发送 confirm

**预期**：

- error_code = `action_actor_mismatch`

### TC-09: workspace mismatch

**步骤**：在 workspace A 生成 token，在 workspace B 确认

**预期**：

- error_code = `workspace_mismatch`

### TC-10: issue 不存在

**步骤**：使用随机 UUID 作为 issue_id

**预期**：

- proposed_action.execution_enabled = false（生成阶段拒绝）

### TC-11: state 不属于 issue project

**步骤**：使用其他 project 的 state_id

**预期**：

- proposed_action.execution_enabled = false

### TC-12: current_state_mismatch

**步骤**：生成 proposed_action 后，手动修改 issue state，再 confirm

**预期**：

- error_code = `current_state_mismatch`

### TC-13: GUEST 用户确认

**步骤**：GUEST 用户发送 confirm

**预期**：

- proposed_action.execution_enabled = false（生成阶段拒绝）

### TC-14: 非 project member 确认

**步骤**：workspace member 但非 project member 发送 confirm

**预期**：

- proposed_action.execution_enabled = false

### TC-15: execution_enabled=false 时确认

**步骤**：直接发送 confirm_action_id（无 valid token）

**预期**：

- error_code = `confirmation_token_invalid`

### TC-16: bulk/delete/archive 仍被拒绝

**步骤**：prompt 包含 "delete issue" 或 "bulk update"

**预期**：

- tool not in whitelist → rejected

---

## 6. 安全检查

| 检查项                                    | 验证方式            |
| ----------------------------------------- | ------------------- |
| 不调用 stdio write                        | 代码审查 + 日志检查 |
| 不调用 plane-mcp-server write             | 代码审查 + 日志检查 |
| 不使用 workspace API key                  | 代码审查            |
| 不返回 raw prompt/result                  | 响应检查            |
| 不返回 confirmation_token 到日志          | 日志检查            |
| 不把 confirmation_token 写入 AIAuditEvent | DB 查询             |
| 不返回 traceback                          | 响应检查            |
| 错误只返回 error_code                     | 响应检查            |
| 不更新 state 以外字段                     | issue 对比检查      |

---

## 7. 回滚方案

| 步骤               | 说明                                                                 |
| ------------------ | -------------------------------------------------------------------- |
| 测试前             | 记录 issue 原始 `state_id`                                           |
| 测试后             | 通过 Plane UI 或 API 将 issue state 改回原值                         |
| 失败恢复           | 同上                                                                 |
| 确认无额外字段改动 | 对比 issue 的 `updated_at`, `completed_at`, `name`, `description` 等 |
| 数据库备份         | 建议测试前备份（非必须，测试 issue 可丢弃）                          |
| 推荐               | 使用一次性测试 issue                                                 |

---

## 8. Runtime 测试步骤

### 8.1 启动 dev 环境

```bash
# 启动 Django + Celery
cd apps/api
python manage.py migrate
python manage.py runserver
celery -A plane worker -l info
```

### 8.2 确认 API 可访问

```bash
curl -s http://localhost:8000/api/workspaces/<slug>/ai-assistant/ \
  -H "Cookie: <session>" | python3 -m json.tool
```

### 8.3 获取测试数据

```bash
# 获取 issue
curl -s http://localhost:8000/api/workspaces/<slug>/projects/<project_id>/issues/ \
  -H "Cookie: <session>" | python3 -m json.tool

# 获取 states
curl -s http://localhost:8000/api/workspaces/<slug>/projects/<project_id>/states/ \
  -H "Cookie: <session>" | python3 -m json.tool
```

### 8.4 发起 proposed_action 请求

```bash
curl -s -X POST http://localhost:8000/api/workspaces/<slug>/ai-assistant/ \
  -H "Cookie: <session>" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "change state <issue_id> to <state_b_id>", "task": "chat", "mode": "mcp"}' \
  | python3 -m json.tool
```

**保存**：`action_id` 和 `confirmation_token`

### 8.5 发起 confirm 请求

```bash
curl -s -X POST http://localhost:8000/api/workspaces/<slug>/ai-assistant/ \
  -H "Cookie: <session>" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "", "task": "chat", "mode": "mcp", "confirm_action_id": "<action_id>", "confirmation_token": "<token>"}' \
  | python3 -m json.tool
```

### 8.6 检查 issue state

```bash
curl -s http://localhost:8000/api/workspaces/<slug>/projects/<project_id>/issues/<issue_id>/ \
  -H "Cookie: <session>" | python3 -m json.tool
```

### 8.7 检查 audit event

```bash
curl -s "http://localhost:8000/api/workspaces/<slug>/ai-audit-events/?event=ai.write.executed" \
  -H "Cookie: <session>" | python3 -m json.tool
```

### 8.8 恢复原 state

```bash
curl -s -X PATCH http://localhost:8000/api/workspaces/<slug>/projects/<project_id>/issues/<issue_id>/ \
  -H "Cookie: <session>" \
  -H "Content-Type: application/json" \
  -d '{"state": "<original_state_id>"}' | python3 -m json.tool
```

### 8.9 记录测试结果

记录每个 TC 的实际结果与预期是否一致。

---

## 9. 禁止事项

| 禁止               | 说明               |
| ------------------ | ------------------ |
| 生产数据测试       | ❌                 |
| 真实确认请求执行   | ❌（本阶段只设计） |
| 数据修改           | ❌（本阶段只设计） |
| migration          | ❌                 |
| Docker 修改        | ❌                 |
| push               | ❌                 |
| PR                 | ❌                 |
| token/API key 输出 | ❌                 |

---

## 10. 是否执行真实测试

**否。** 本阶段只设计测试计划。

---

## 11. 是否修改数据

**否。**

---

## 12. 是否新增 migration

**否。**

---

## 13. 是否修改 Docker

**否。**

---

## 14. 是否可以进入 Phase 9.3.7

**是。** 测试计划完成，可在 dev 环境中执行手动测试。

---

## 15. Phase 9.3.7 Preflight 记录（2026-05-28）

Phase 9.3.7 完成了 runtime preflight 检查，详见 [`PHASE_9_3_7_CONFIRMED_STATE_UPDATE_RUNTIME_PREFLIGHT_REPORT.md`](./PHASE_9_3_7_CONFIRMED_STATE_UPDATE_RUNTIME_PREFLIGHT_REPORT.md)。

**Preflight 结果**：

- ✅ 开发 fork 路径确认
- ✅ API 可访问
- ⚠️ AI 功能未启用（需设置 Docker 环境变量）
- ❌ 测试数据未选择（环境未就绪）
