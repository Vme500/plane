# 第 8.5 阶段报告：Admin-Only AI Audit Read API Design

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：设计完成，未写代码

---

## 1. 当前分支和 commit

| 项目        | 值                                                               |
| ----------- | ---------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                           |
| 最新 commit | `83c532c6d7` — `docs: validate AI audit event migration dry run` |
| 工作区状态  | 干净（无未提交修改）                                             |

---

## 2. 现有 API/serializer/permission 风格调研

### Endpoint 风格

| 项目     | 说明                                                               |
| -------- | ------------------------------------------------------------------ |
| 基类     | `BaseAPIView`（`plane.app.views.base`）                            |
| 装饰器   | `@allow_permission(allowed_roles=[ROLE.ADMIN], level="WORKSPACE")` |
| URL 风格 | `workspaces/<str:slug>/ai-assistant/`                              |
| URL 文件 | `apps/api/plane/app/urls/external.py`                              |

### Serializer 风格

| 项目     | 说明                                              |
| -------- | ------------------------------------------------- |
| 基类     | `BaseSerializer` 或 `serializers.ModelSerializer` |
| 文件位置 | `apps/api/plane/app/serializers/`                 |
| 命名     | `{Entity}Serializer` / `{Entity}LiteSerializer`   |

### Permission 风格

| 项目           | 说明                                                                            |
| -------------- | ------------------------------------------------------------------------------- |
| ADMIN only     | `@allow_permission(allowed_roles=[ROLE.ADMIN], level="WORKSPACE")`              |
| ADMIN + MEMBER | `@allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")` |
| ROLE 枚举      | `ADMIN=20, MEMBER=15, GUEST=5`                                                  |

### Pagination 风格

Plane 使用 `per_page` query parameter + cursor-based pagination in some APIs, and page-based in others.

---

## 3. 推荐 endpoint

| 项目            | 值                                                      |
| --------------- | ------------------------------------------------------- |
| 路径            | `GET /api/workspaces/<str:slug>/ai-audit-events/`       |
| Method          | GET                                                     |
| 权限            | workspace ADMIN only                                    |
| URL 文件        | `apps/api/plane/app/urls/external.py`（或新增 `ai.py`） |
| View 文件       | `apps/api/plane/app/views/ai.py`（新文件）              |
| Serializer 文件 | `apps/api/plane/app/serializers/ai.py`（新文件）        |

---

## 4. 权限设计

| 角色                | 访问      | 返回                           |
| ------------------- | --------- | ------------------------------ |
| Workspace ADMIN     | ✅ 可查看 | 200 + 数据                     |
| Workspace MEMBER    | ❌ 禁止   | 403                            |
| Workspace GUEST     | ❌ 禁止   | 403                            |
| 非 workspace member | ❌ 禁止   | 404（不暴露 workspace 存在性） |

### 实现方式

```python
@allow_permission(allowed_roles=[ROLE.ADMIN], level="WORKSPACE")
def get(self, request, slug):
    ...
```

使用现有 `allow_permission` 装饰器，与 Plane 现有风格一致。

---

## 5. Query Filters

| 参数                | 类型     | 说明                                         |
| ------------------- | -------- | -------------------------------------------- |
| `event`             | string   | 按事件类型筛选                               |
| `mode`              | string   | `standard` / `mcp`                           |
| `adapter`           | string   | `none` / `mock` / `stdio`                    |
| `tool_name`         | string   | 按工具名筛选                                 |
| `tool_status`       | string   | `success` / `blocked` / `error` / `rejected` |
| `actor_id`          | UUID     | 按操作用户筛选                               |
| `source`            | string   | 按来源筛选                                   |
| `error_code`        | string   | 按错误码筛选                                 |
| `write_operation`   | boolean  | 按写操作标记筛选                             |
| `readonly`          | boolean  | 按只读标记筛选                               |
| `created_at_after`  | datetime | 时间范围起始（ISO 8601）                     |
| `created_at_before` | datetime | 时间范围结束（ISO 8601）                     |
| `page`              | int      | 页码                                         |
| `per_page`          | int      | 每页数量                                     |

### 时间范围限制

- 默认查询最近 **30 天**
- 最大时间范围 **90 天**
- 超出范围返回 400 错误

---

## 6. Response Serializer 字段

| 字段                  | 类型     | 说明                                 |
| --------------------- | -------- | ------------------------------------ |
| `id`                  | UUID     | 事件 ID                              |
| `created_at`          | datetime | 创建时间                             |
| `workspace_id`        | UUID     | workspace ID                         |
| `actor`               | object   | `{id, display_name, email}`          |
| `event`               | string   | 事件类型                             |
| `mode`                | string   | standard / mcp                       |
| `adapter`             | string   | none / mock / stdio                  |
| `tool_name`           | string   | 工具名                               |
| `tool_status`         | string   | success / blocked / error / rejected |
| `readonly`            | boolean  | 是否只读                             |
| `permission_filtered` | boolean  | 是否经过权限过滤                     |
| `raw_result_returned` | boolean  | 是否返回 raw result                  |
| `write_operation`     | boolean  | 是否写操作                           |
| `duration_ms`         | int      | 请求耗时                             |
| `item_count`          | int      | 返回 item 数量                       |
| `prompt_length`       | int      | prompt 字符数                        |
| `error_code`          | string   | 错误码                               |
| `source`              | string   | 来源                                 |
| `request_id`          | string   | 请求追踪 ID                          |

### Actor 字段脱敏

```python
class ActorLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "display_name", "email"]
```

- `id`：UUID
- `display_name`：first_name + last_name
- `email`：可选，ADMIN 可见

---

## 7. 禁止返回字段

| 字段                                | 原因                   |
| ----------------------------------- | ---------------------- |
| raw prompt                          | 隐私（model 中不存在） |
| raw result                          | 隐私（model 中不存在） |
| raw MCP result                      | 安全（model 中不存在） |
| token / API key / cookie / password | secret                 |
| request headers                     | 安全                   |
| stack trace / env                   | 安全                   |
| full user object                    | 隐私                   |
| full model object                   | 安全                   |
| deleted_at                          | 无必要                 |
| created_by / updated_by             | 无必要                 |

---

## 8. Pagination / Ordering

| 项目           | 值                                  |
| -------------- | ----------------------------------- |
| 默认 ordering  | `created_at` DESC                   |
| 默认 page size | 20                                  |
| 最大 page size | 100                                 |
| 分页方式       | page-based（`?page=2&per_page=50`） |

---

## 9. 性能设计

| 项目                  | 策略                         |
| --------------------- | ---------------------------- |
| 必须分页              | ✅                           |
| 必须 workspace filter | ✅                           |
| 使用 Phase 8.4 索引   | ✅ `idx_ai_audit_ws_created` |
| select_related        | `actor`, `workspace`         |
| 避免大查询            | 时间范围限制 90 天 + 分页    |
| 额外索引              | 暂不新增                     |
| 导出                  | 后置                         |

---

## 10. Retention 设计

| 项目                  | 值                                                                     |
| --------------------- | ---------------------------------------------------------------------- |
| 默认保留期            | 90 天                                                                  |
| 自动清理              | Phase 8.7+ 实现                                                        |
| 清理方式              | Django management command                                              |
| 删除策略              | **hard delete**（audit 数据不需要 soft delete）                        |
| BaseModel soft delete | 不适合 audit retention（会永久保留 deleted_at 非空记录）               |
| 物理删除              | 建议使用 `AIAuditEvent.objects.filter(created_at__lt=cutoff).delete()` |

---

## 11. 安全与隐私要求

| 要求                                 | 实现                                 |
| ------------------------------------ | ------------------------------------ |
| 不返回 raw prompt                    | ✅ model 中不存在                    |
| 不返回 raw result                    | ✅ model 中不存在                    |
| 不返回 raw MCP result                | ✅ model 中不存在                    |
| 不返回 token/API key/cookie/password | ✅                                   |
| 不返回 headers                       | ✅                                   |
| 不返回 stack/env                     | ✅                                   |
| admin-only                           | ✅ `@allow_permission([ROLE.ADMIN])` |
| workspace scoped                     | ✅ `workspace__slug=slug`            |
| pagination                           | ✅                                   |
| 不支持 unrestricted export           | ✅                                   |
| 不做写操作                           | ✅                                   |

---

## 12. Phase 8.6 实施边界

### Phase 8.6 可以做

- Serializer（`AIAuditEventSerializer`, `ActorLiteSerializer`）
- Admin-only list endpoint（`AIAuditEventListEndpoint`）
- URL route
- Pagination / filter
- docs
- py_compile 验证

### Phase 8.6 不做

- Frontend UI
- Retention job
- Export
- Write operation
- Docker
- Migration（除非发现缺索引且先确认）
- Production migrate

---

## 13. 是否新增 migration

**Phase 8.5 不需要。Phase 8.6 可能需要（如果发现缺索引）。**

---

## 14. 是否修改 Docker

**否。**

---

## 15. 是否实现写操作

**否。**

---

## 16. 是否可以进入 Phase 8.6

**是。** 设计完成，可实现 serializer + endpoint + route。

---

## 17. Phase 8.6 实施记录（2026-05-28）

Phase 8.6 已按本文档设计实施，详见 [`PHASE_8_6_AUDIT_READ_API_IMPLEMENTATION_REPORT.md`](./PHASE_8_6_AUDIT_READ_API_IMPLEMENTATION_REPORT.md)。

**实施结果**：

- ✅ AIAuditEventSerializer + ActorLiteSerializer
- ✅ AIAuditEventListEndpoint（GET, ADMIN only）
- ✅ URL route + 12 filters + pagination
- ✅ py_compile 通过
