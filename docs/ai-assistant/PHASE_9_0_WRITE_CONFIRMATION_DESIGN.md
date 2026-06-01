# 第 9.0 阶段报告：AI/MCP Write Operation Confirmation Design

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：设计完成，未写代码

---

## 1. 当前分支和 commit

| 项目        | 值                                                                 |
| ----------- | ------------------------------------------------------------------ |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                             |
| 最新 commit | `7149da45d7` — `docs: validate AI audit retention cleanup command` |
| 工作区状态  | 干净（无未提交修改）                                               |

---

## 2. 当前 read-only/write rejection 状态

### Read-only tools（Phase 6 白名单）

- `get_me`
- `list_projects`
- `retrieve_project`
- `list_work_items`
- `search_work_items`
- `retrieve_work_item`
- `list_states`
- `list_labels`
- `list_cycles`
- `list_modules`

### Write rejection mechanism

| 层                    | 机制                                                        |
| --------------------- | ----------------------------------------------------------- |
| `is_tool_allowed()`   | 白名单检查                                                  |
| `PROHIBITED_PATTERNS` | create/update/delete/assign/move/archive/bulk/import/upload |
| stdio safety gate     | 只允许 get_me/list_projects/retrieve_project                |
| audit event           | `ai.tool.rejected` + `write_operation=True`                 |

---

## 3. 写操作风险分级

### 低风险

| 操作             | 说明                       |
| ---------------- | -------------------------- |
| create work item | 需要 title + project，单条 |
| add comment      | 内容可能含敏感文本         |

### 中风险

| 操作                   | 说明                                   |
| ---------------------- | -------------------------------------- |
| update work item title | 需要校验权限                           |
| update work item state | 需要校验 state 属于同一 project        |
| assign work item       | 需要校验 assignee 是 project member    |
| update priority        | 单字段更新                             |
| add/remove label       | 需要校验 label 属于同一 project        |
| move to cycle/module   | 需要校验 cycle/module 属于同一 project |

### 高风险（Phase 9.1 禁止）

| 操作                        | 原因            |
| --------------------------- | --------------- |
| delete/archive issue        | 数据丢失        |
| bulk update                 | 批量操作不可逆  |
| delete project/cycle/module | 数据丢失        |
| change workspace settings   | 影响全局        |
| change permissions/members  | 安全边界        |
| API key/integration changes | secret 泄露风险 |

---

## 4. Confirmation Workflow

### 二阶段流程

```
第一阶段：Plan Only
  用户 → AI prompt → MCP tool 解析 → proposed_action → confirmation card
  不执行写操作
  记录 ai.write.proposed

第二阶段：Explicit Confirm
  用户点击 Confirm → 后端重新校验 → 执行 → 返回结果
  记录 ai.write.executed 或 ai.write.rejected
```

### 流程图

```
User: "创建一个 bug: 登录页面崩溃"
  ↓
AI parses → proposed_action:
  action_type: create_work_item
  target_type: work_item
  project_id: xxx
  title: "登录页面崩溃"
  state_id: yyy (default)
  priority: urgent
  ↓
Backend returns confirmation card
  ↓
User sees: "创建 Work Item: 登录页面崩溃 (project: MyProject)"
  [Confirm] [Cancel]
  ↓
User clicks Confirm
  ↓
Backend re-validates permissions + target existence
  ↓
Execute create_work_item via Plane API/service
  ↓
Return result
```

---

## 5. proposed_action Schema

| 字段                    | 类型     | 说明                                          |
| ----------------------- | -------- | --------------------------------------------- |
| `action_id`             | UUID     | 唯一标识                                      |
| `workspace_slug`        | string   | workspace scope                               |
| `actor_id`              | UUID     | 操作用户                                      |
| `action_type`           | string   | create_work_item / update_state / add_comment |
| `target_type`           | string   | work_item / comment / project                 |
| `target_id`             | UUID     | 目标 ID（update 时）                          |
| `target_display`        | string   | 目标显示名                                    |
| `current_value`         | string   | 当前值（update 时）                           |
| `proposed_value`        | string   | 拟设值                                        |
| `risk_level`            | string   | low / medium                                  |
| `summary`               | string   | 人类可读摘要                                  |
| `requires_confirmation` | bool     | 始终 true                                     |
| `expires_at`            | datetime | 过期时间（建议 5 分钟）                       |
| `readonly_preview`      | bool     | 始终 true（第一阶段）                         |
| `safety_flags`          | object   | 安全标记                                      |

### 禁止字段

raw prompt, raw result, raw MCP result, token, API key, cookie, password, headers, stack trace, env, full request/response body.

---

## 6. Phase 9.1 推荐最小写操作

### 方案比较

| 方案 | 操作                   | 优点         | 缺点               |
| ---- | ---------------------- | ------------ | ------------------ |
| A    | create work item       | 风险低，常用 | 需要多个参数       |
| B    | update work item state | 常用，单字段 | 需要校验 state     |
| C    | add comment            | 风险低       | 内容敏感，审计困难 |

### 推荐

**Phase 9.1 只实现方案 B：update work item state。**

理由：

1. 最常用的写操作
2. 单字段更新，参数简单
3. 可通过 Plane 现有权限校验
4. 目标 state 必须属于同一 project，天然限制
5. 不涉及敏感文本内容

---

## 7. 权限设计

| 要求                              | 实现                                 |
| --------------------------------- | ------------------------------------ |
| 使用 request.user                 | ✅ 不能用 workspace API key          |
| 校验 workspace membership         | ✅ `WorkspaceMember`                 |
| 校验 project membership           | ✅ `ProjectMember`                   |
| 校验 issue 属于 workspace/project | ✅ `Issue.issue_objects.filter(...)` |
| GUEST 禁止写                      | ✅ `ROLE.MEMBER` 最低                |
| 阻止跨 workspace target           | ✅ queryset filter                   |
| stdio adapter 不直接执行写        | ✅ 写操作走 Plane 内部权限校验路径   |

### 关键：stdio adapter 不适合写操作

plane-mcp-server 使用 workspace API key，无法表达当前用户权限。写操作必须走 Plane 内部权限校验，不能依赖 stdio adapter。

---

## 8. Audit Logging 设计

### 新增 event 类型

| event                | 说明                      |
| -------------------- | ------------------------- |
| `ai.write.proposed`  | 写操作提案生成            |
| `ai.write.confirmed` | 用户确认                  |
| `ai.write.executed`  | 写操作执行成功            |
| `ai.write.rejected`  | 写操作被拒绝（权限/安全） |
| `ai.write.expired`   | 确认 token 过期           |
| `ai.write.error`     | 写操作执行失败            |

### 字段

使用现有 AIAuditEvent schema：

- `event`: ai.write.\*
- `tool_name`: 具体操作名
- `tool_status`: success/blocked/error/rejected
- `readonly`: false
- `write_operation`: true
- `permission_filtered`: true

### Phase 9.1 是否需要新增 migration

**否。** 现有 AIAuditEvent schema 足够记录 write events。不需要 target_type/target_id 字段（通过 tool_name + error_code 记录）。

---

## 9. API Contract 方案比较

| 方案 | 说明                  | 优点              | 缺点           |
| ---- | --------------------- | ----------------- | -------------- |
| A    | 复用 /ai-assistant/   | 简单，单 endpoint | 语义不清       |
| B    | 新增 confirm endpoint | 语义清晰          | 多 route       |
| C    | 前端本地确认          | —                 | 不安全，不推荐 |

### 推荐

**Phase 9.1 使用方案 A：复用 /ai-assistant/。**

实现：

1. 第一次请求（mode=mcp, tool=update_state）→ 返回 proposed_action
2. 第二次请求（mode=mcp, tool=update_state, confirm_action_id=xxx）→ 执行

---

## 10. 前端 Confirmation Card 设计

### 显示内容

- action summary: "更新 Work Item 状态"
- target: "登录页面崩溃"
- current value: "Todo"
- proposed value: "In Progress"
- risk level: "Medium"
- expires_at: "5 分钟内有效"
- [Confirm] button
- [Cancel] button

### 禁止显示

raw prompt, raw MCP result, secret, headers, stack trace。

### 行为

- 用户必须显式点击 Confirm
- 不能用模糊文本自动执行
- Cancel 记录 ai.write.rejected
- timeout 后不能执行

---

## 11. 失败与并发设计

| 场景              | 处理                                                 |
| ----------------- | ---------------------------------------------------- |
| target 已不存在   | 返回 404，记录 ai.write.rejected                     |
| state 已变化      | 返回 409 Conflict，要求重新确认                      |
| 用户权限变化      | 重新校验，无权限返回 403                             |
| action token 过期 | 返回 410 Gone，记录 ai.write.expired                 |
| 重复点击确认      | idempotency key（action_id），第二次返回已有结果     |
| 后端执行失败      | 返回 500，记录 ai.write.error                        |
| LLM 输出不可信    | 后端必须重新校验所有参数，不信任前端传入的 target_id |

---

## 12. Prompt Injection 防护

| 风险               | 防护                                                      |
| ------------------ | --------------------------------------------------------- |
| "直接执行不用确认" | 后端强制 confirmation flow，不接受 skip_confirm 参数      |
| "忽略之前的指令"   | proposed_action 由后端生成，不依赖 LLM 输出的 action 参数 |
| "以管理员身份执行" | 后端使用 request.user，不接受前端传入的 actor_id          |
| "修改 target_id"   | 后端重新校验 target 存在性和权限                          |

---

## 13. 禁止操作清单（Phase 9.1）

| 操作                        | 状态          |
| --------------------------- | ------------- |
| delete/archive issue        | ❌ 禁止       |
| bulk update                 | ❌ 禁止       |
| delete project/cycle/module | ❌ 禁止       |
| change workspace settings   | ❌ 禁止       |
| change permissions/members  | ❌ 禁止       |
| API key/integration changes | ❌ 禁止       |
| create work item            | ⏳ Phase 9.2+ |
| add comment                 | ⏳ Phase 9.2+ |
| update work item state      | ✅ Phase 9.1  |

---

## 14. Phase 9.1 实施边界

### Phase 9.1 可以做

- proposed_action schema
- update work item state（单条）
- backend confirmation flow
- pi-chat confirmation card
- audit events（ai.write.\*）
- no stdio write execution
- no bulk
- no delete/archive

### Phase 9.1 不做

- bulk update
- delete/archive
- permission/member/settings/API key changes
- unrestricted tool execution
- direct stdio write tools
- audit UI
- Docker
- production migrate

---

## 15. 是否新增 migration

**Phase 9.0 不新增。Phase 9.1 不需要新增（现有 AIAuditEvent schema 足够）。**

---

## 16. 是否修改 Docker

**否。**

---

## 17. 是否实现写操作

**否。** Phase 9.0 只做设计。

---

## 18. 是否可以进入 Phase 9.1

**是。** 设计完成，可实现 update work item state + confirmation flow。

---

## 19. Phase 9.1 实施记录（2026-05-28）

Phase 9.1 已按本文档设计实施 plan-only confirmation，详见 [`PHASE_9_1_WRITE_CONFIRMATION_PLAN_ONLY_REPORT.md`](./PHASE_9_1_WRITE_CONFIRMATION_PLAN_ONLY_REPORT.md)。

**实施结果**：

- ✅ 写意图检测
- ✅ proposed_action 生成（execution_enabled=False）
- ✅ confirm_action_id 拦截
- ✅ pi-chat confirmation card
- ✅ 不执行真实写操作
