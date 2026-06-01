# 第 9.2 阶段报告：Confirmed update_work_item_state Implementation Design

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：设计完成，未写代码

---

## 1. 当前分支和 commit

| 项目        | 值                                                            |
| ----------- | ------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                        |
| 最新 commit | `eccf13239d` — `docs: validate AI write confirmation preview` |
| 工作区状态  | 干净（无未提交修改）                                          |

---

## 2. Plane issue/work item/state update path 调研

### Issue Model

| 项目         | 说明                                                                          |
| ------------ | ----------------------------------------------------------------------------- |
| Model 名     | `Issue`（继承 `ProjectBaseModel`）                                            |
| state 字段   | `state = ForeignKey("db.State")`，DB 列名 `state_id`                          |
| 变更追踪     | `ChangeTrackerMixin`，`TRACKED_FIELDS = ["state_id"]`                         |
| 自动逻辑     | `_sync_completed_at()` — state 变为 completed group 时自动设置 `completed_at` |
| workspace FK | 直接有（通过 `ProjectBaseModel`）                                             |

### State Model

| 项目     | 说明                                                                                 |
| -------- | ------------------------------------------------------------------------------------ |
| Model 名 | `State`（继承 `ProjectBaseModel`）                                                   |
| 关键字段 | `name`, `group` (backlog/unstarted/started/completed/cancelled/triage), `project` FK |
| 唯一约束 | `(name, project)` when `deleted_at__isnull=True`                                     |
| 管理器   | `State.objects`（排除 triage）, `State.all_state_objects`（全部）                    |

### Issue Update 流程

1. 获取 issue: `Issue.objects.get(workspace__slug=slug, project_id=project_id, pk=pk)`
2. 创建 partial serializer: `IssueSerializer(issue, data={"state": new_state_id}, partial=True)`
3. `serializer.save()` — 触发 `_sync_completed_at()`
4. 派发 `issue_activity.delay()` — 创建 IssueActivity 记录
5. 派发 `model_activity.delay()` — 触发 webhooks

### 权限

| 项目              | 说明                                                                      |
| ----------------- | ------------------------------------------------------------------------- |
| 权限类            | `ProjectEntityPermission`                                                 |
| 要求              | `ProjectMember` with `role__in=[ADMIN(20), MEMBER(15)]`, `is_active=True` |
| GUEST(5)          | ❌ 禁止                                                                   |
| 非 project member | ❌ 禁止                                                                   |

---

## 3. Target/State 解析设计

### Target 解析

| 来源                            | 解析方式                                         |
| ------------------------------- | ------------------------------------------------ |
| issue UUID                      | 直接使用 `Issue.objects.get(pk=uuid)`            |
| issue identifier (如 TOKEN-123) | 通过 `project__identifier` + issue sequence 解析 |
| 模糊标题                        | ❌ 不支持，返回 disambiguation                   |

**Phase 9.3 推荐**：只支持 UUID，不支持 identifier 解析（减少复杂度）。

### State 解析

| 来源       | 解析方式                                                     |
| ---------- | ------------------------------------------------------------ |
| state UUID | 直接使用 `State.objects.get(pk=uuid, project_id=...)`        |
| state name | `State.objects.get(name=name, project_id=...)`（需唯一匹配） |

**Phase 9.3 推荐**：只支持 UUID。

### 校验链

1. issue 必须属于当前 workspace
2. issue 必须属于当前 project
3. proposed state 必须属于同一 project
4. current state 必须重新从 DB 读取
5. confirm 时必须重新校验 current state 是否一致

---

## 4. Confirm Token/Action_ID 方案比较

| 方案                      | 说明                        | 优点                 | 缺点              |
| ------------------------- | --------------------------- | -------------------- | ----------------- |
| A: signed payload         | Django TimestampSigner 签名 | 不落库，无 migration | 需要管理签名密钥  |
| B: Redis cache            | action_id 存 Redis          | 简单                 | 依赖 Redis 可用性 |
| C: DB PendingAction model | 数据库持久化                | 最稳                 | 需要 migration    |

### 推荐

**Phase 9.3 使用方案 A：signed payload。**

理由：

1. 不需要 migration
2. 不依赖 Redis
3. Django 内置 `TimestampSigner` 支持过期检查
4. 签名防篡改
5. payload 包含 workspace_slug 防跨 workspace 重放

### Signed Payload 设计

```python
from django.core.signing import TimestampSigner

signer = TimestampSigner()

# Generate
payload = {
    "workspace_slug": workspace_slug,
    "actor_id": str(user.id),
    "issue_id": str(issue.id),
    "project_id": str(issue.project_id),
    "current_state_id": str(issue.state_id),
    "proposed_state_id": str(proposed_state_id),
    "action_type": "update_work_item_state",
}
token = signer.sign(json.dumps(payload))

# Verify
raw = signer.unsign(token, max_age=300)  # 5 minutes
data = json.loads(raw)
```

### 防护机制

| 风险              | 防护                                              |
| ----------------- | ------------------------------------------------- |
| 篡改              | TimestampSigner 签名验证                          |
| 跨 workspace 重放 | payload 包含 workspace_slug，verify 时检查        |
| 用户 A 确认用户 B | payload 包含 actor_id，verify 时检查 request.user |
| 过期执行          | `max_age=300`（5 分钟）                           |
| 重复执行          | 幂等：设置相同 state 结果相同                     |

---

## 5. 真实执行路径

### 推荐：直接 ORM + 手动派发 activity

Phase 9.3 不使用 API serializer（避免序列化/反序列化开销），直接使用 ORM：

```python
# 1. Verify token
payload = verify_signed_token(token)

# 2. Verify actor
assert str(user.id) == payload["actor_id"]

# 3. Verify workspace
assert workspace_slug == payload["workspace_slug"]

# 4. Verify workspace membership
assert WorkspaceMember.objects.filter(
    workspace__slug=workspace_slug, member=user, is_active=True
).exists()

# 5. Verify project membership (ADMIN or MEMBER)
assert ProjectMember.objects.filter(
    project_id=payload["project_id"],
    member=user,
    role__in=[20, 15],  # ADMIN, MEMBER
    is_active=True,
).exists()

# 6. Verify issue exists and belongs to workspace/project
issue = Issue.objects.get(
    pk=payload["issue_id"],
    workspace__slug=workspace_slug,
    project_id=payload["project_id"],
)

# 7. Verify current state unchanged
assert str(issue.state_id) == payload["current_state_id"]

# 8. Verify proposed state belongs to same project
new_state = State.objects.get(
    pk=payload["proposed_state_id"],
    project_id=payload["project_id"],
)

# 9. Capture old state for activity
old_state_id = str(issue.state_id)

# 10. Update
issue.state_id = new_state.id
issue.save()  # Triggers _sync_completed_at()

# 11. Dispatch activity (if Celery available)
try:
    from plane.bgtasks.issue_activities_task import issue_activity
    issue_activity.delay(
        type="issue.activity.updated",
        requested_data=json.dumps({"state_id": str(new_state.id)}),
        current_instance=json.dumps({"state_id": old_state_id}),
        issue_id=str(issue.id),
        actor_id=str(user.id),
        project_id=str(issue.project_id),
        workspace_slug=workspace_slug,
    )
except Exception:
    pass  # Activity logging is best-effort
```

---

## 6. 权限校验设计

| 层                         | 检查                                                                                          |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| Workspace membership       | `WorkspaceMember.objects.filter(workspace__slug=slug, member=user, is_active=True)`           |
| Project membership         | `ProjectMember.objects.filter(project_id=..., member=user, role__in=[20,15], is_active=True)` |
| Issue belongs to workspace | `Issue.objects.get(pk=..., workspace__slug=slug)`                                             |
| Issue belongs to project   | `Issue.objects.get(pk=..., project_id=...)`                                                   |
| State belongs to project   | `State.objects.get(pk=..., project_id=...)`                                                   |

**不使用**：

- workspace API key
- stdio adapter
- LLM 结果决定权限

---

## 7. API Contract

### 第一次请求（proposed_action）

```json
{
  "mcp_preview": {
    "proposed_action": {
      "action_id": "uuid",
      "confirmation_token": "signed-token",
      "action_type": "update_work_item_state",
      "target_type": "work_item",
      "target_id": "issue-uuid",
      "target_display": "Issue Title",
      "current_value": "Todo",
      "proposed_value": "In Progress",
      "risk_level": "medium",
      "summary": "Update state: Todo → In Progress",
      "requires_confirmation": true,
      "expires_at": "2026-05-28T12:05:00Z",
      "execution_enabled": true
    }
  }
}
```

### 第二次请求（confirm）

```json
{
  "mode": "mcp",
  "confirm_action_id": "uuid",
  "confirmation_token": "signed-token"
}
```

### 成功响应

```json
{
  "response": "State updated: Todo → In Progress",
  "mcp_preview": {
    "tool": { "name": "update_work_item_state", "status": "executed", "readonly": false },
    "summary": "State updated successfully",
    "proposed_action": null
  }
}
```

### 失败响应

```json
{
  "response": "Error: current state has changed since proposal",
  "mcp_preview": {
    "tool": { "name": "update_work_item_state", "status": "error", "readonly": false },
    "summary": "Current state mismatch",
    "proposed_action": null
  }
}
```

---

## 8. Audit Events

| event                | 触发条件                   |
| -------------------- | -------------------------- |
| `ai.write.proposed`  | 生成 proposed_action       |
| `ai.write.confirmed` | 用户发送 confirm_action_id |
| `ai.write.executed`  | 写操作成功                 |
| `ai.write.rejected`  | 权限/验证失败              |
| `ai.write.expired`   | token 过期                 |
| `ai.write.error`     | 执行异常                   |

使用现有 AIAuditEvent schema，不需要新增 migration。

---

## 9. Error Codes

| error_code                    | 说明                       |
| ----------------------------- | -------------------------- |
| `execution_not_enabled`       | Phase 9.1 使用             |
| `confirmation_token_invalid`  | 签名验证失败               |
| `confirmation_token_expired`  | max_age 超时               |
| `action_actor_mismatch`       | request.user != actor_id   |
| `workspace_mismatch`          | workspace slug 不一致      |
| `workspace_member_required`   | 非 workspace member        |
| `project_permission_denied`   | 非 project member 或 GUEST |
| `issue_not_found`             | issue 不存在               |
| `issue_workspace_mismatch`    | issue 不属于当前 workspace |
| `state_not_found`             | state 不存在               |
| `state_project_mismatch`      | state 不属于同一 project   |
| `current_state_mismatch`      | issue state 已变化         |
| `write_operation_not_allowed` | 通用写操作拒绝             |
| `write_execution_failed`      | 执行异常                   |
| `unknown_error`               | 未知错误                   |

---

## 10. 前端确认 UI 更新设计

| 状态                      | UI                                          |
| ------------------------- | ------------------------------------------- |
| `execution_enabled=false` | Confirm disabled（Phase 9.1）               |
| `execution_enabled=true`  | Confirm 可点击                              |
| Confirm 点击              | 发送 confirm_action_id + confirmation_token |
| 执行中                    | loading spinner                             |
| 成功                      | 显示 "State updated: X → Y"                 |
| 失败                      | 显示错误原因                                |
| 过期                      | 显示 "Proposal expired"                     |
| Cancel                    | 关闭卡片                                    |

---

## 11. 并发和幂等设计

| 场景                      | 处理                                        |
| ------------------------- | ------------------------------------------- |
| current state 变化        | 返回 `current_state_mismatch`，要求重新提议 |
| 用户重复点击 Confirm      | 幂等：设置相同 state 结果相同               |
| signed payload 可重复执行 | 接受：相同 state 设置是幂等的               |
| 不同用户确认同一 action   | 拒绝：`action_actor_mismatch`               |

---

## 12. 禁止操作清单

| 操作                         | 状态    |
| ---------------------------- | ------- |
| bulk update                  | ❌ 禁止 |
| delete/archive issue         | ❌ 禁止 |
| create issue                 | ❌ 禁止 |
| assign/label/priority        | ❌ 禁止 |
| settings/permissions/API key | ❌ 禁止 |
| stdio write                  | ❌ 禁止 |
| plane-mcp-server write       | ❌ 禁止 |

---

## 13. Phase 9.3 实施边界

### Phase 9.3 可以做

- signed confirmation token
- target/state 解析（UUID only）
- single update_work_item_state
- request.user 权限校验
- internal Plane update path（ORM + activity dispatch）
- front-end enabled Confirm
- audit events
- no migration

### Phase 9.3 不做

- bulk
- delete/archive
- create issue
- assign/label/priority
- settings/permissions/API key
- stdio write
- plane-mcp-server write
- Docker
- audit UI
- production migrate

---

## 14. 是否新增 migration

**Phase 9.2 不新增。Phase 9.3 不需要新增（signed payload 不落库）。**

---

## 15. 是否修改 Docker

**否。**

---

## 16. 是否实现真实写操作

**否。** Phase 9.2 只做设计。

---

## 17. 是否可以进入 Phase 9.3

**是。** 设计完成，可实现 signed confirmation token + 真实 update_work_item_state。
