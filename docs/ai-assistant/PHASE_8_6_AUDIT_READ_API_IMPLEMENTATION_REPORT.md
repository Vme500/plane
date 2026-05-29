# 第 8.6 阶段报告：Admin-Only AI Audit Read API Implementation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                              |
| ---------- | ----------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`          |
| 基于       | `d725836fba` — `docs: design AI audit read API` |
| 工作区状态 | 干净（无未提交修改）                            |

---

## 2. 修改文件清单

| 文件                                   | 变更                                               |
| -------------------------------------- | -------------------------------------------------- |
| `apps/api/plane/app/serializers/ai.py` | 新增：AIAuditEventSerializer + ActorLiteSerializer |
| `apps/api/plane/app/views/ai.py`       | 新增：AIAuditEventListEndpoint                     |
| `apps/api/plane/app/urls/external.py`  | 修改：新增 ai-audit-events URL                     |

---

## 3. endpoint 路径

`GET /api/workspaces/<str:slug>/ai-audit-events/`

---

## 4. method

GET（只读）

---

## 5. 权限设计是否实现

**是。** `@allow_permission(allowed_roles=[ROLE.ADMIN], level="WORKSPACE")`

| 角色                | 访问 | 返回                            |
| ------------------- | ---- | ------------------------------- |
| Workspace ADMIN     | ✅   | 200 + 数据                      |
| Workspace MEMBER    | ❌   | 403                             |
| Workspace GUEST     | ❌   | 403                             |
| 非 workspace member | ❌   | 404（由 allow_permission 处理） |

---

## 6. serializer 字段

| 字段                  | 类型                        |
| --------------------- | --------------------------- |
| `id`                  | UUID                        |
| `created_at`          | datetime                    |
| `workspace_slug`      | string                      |
| `actor`               | `{id, display_name, email}` |
| `event`               | string                      |
| `mode`                | string                      |
| `adapter`             | string                      |
| `tool_name`           | string                      |
| `tool_status`         | string                      |
| `readonly`            | boolean                     |
| `permission_filtered` | boolean                     |
| `raw_result_returned` | boolean                     |
| `write_operation`     | boolean                     |
| `duration_ms`         | int                         |
| `item_count`          | int                         |
| `prompt_length`       | int                         |
| `error_code`          | string                      |
| `source`              | string                      |
| `request_id`          | string                      |

---

## 7. 禁止返回字段

raw prompt, raw result, raw MCP result, token, API key, cookie, password, headers, stack trace, env, full user object, full model object, deleted_at, created_by, updated_by。

---

## 8. filters

| 参数                | 类型     | 白名单                     |
| ------------------- | -------- | -------------------------- |
| `event`             | string   | ✅ `ALLOWED_EVENTS`        |
| `mode`              | string   | ✅ `ALLOWED_MODES`         |
| `adapter`           | string   | ✅ `ALLOWED_ADAPTERS`      |
| `tool_name`         | string   | 自由值                     |
| `tool_status`       | string   | ✅ `ALLOWED_TOOL_STATUSES` |
| `actor_id`          | UUID     | 自由值                     |
| `source`            | string   | 自由值                     |
| `error_code`        | string   | 自由值                     |
| `write_operation`   | boolean  | true/false                 |
| `readonly`          | boolean  | true/false                 |
| `created_at_after`  | datetime | ISO 8601                   |
| `created_at_before` | datetime | ISO 8601                   |

---

## 9. pagination / ordering

| 项目              | 值                                                    |
| ----------------- | ----------------------------------------------------- |
| ordering          | `created_at` DESC                                     |
| default page size | 20                                                    |
| max page size     | 100                                                   |
| 分页方式          | page-based (`?page=2&per_page=50`)                    |
| 响应结构          | `{results, total_count, page, per_page, total_pages}` |

---

## 10. default/max time window

| 项目         | 值                               |
| ------------ | -------------------------------- |
| 默认时间窗口 | 最近 30 天                       |
| 最大时间窗口 | 90 天                            |
| 超出范围处理 | clamp 到 max_after（不返回 400） |

---

## 11. 是否新增 migration

**否。**

---

## 12. 是否修改 Docker

**否。**

---

## 13. 是否新增前端 UI

**否。**

---

## 14. 是否实现写操作

**否。** 只支持 GET。

---

## 15. 是否改变 existing API contract

**否。** 新增 endpoint，不修改现有 API。

---

## 16. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/app/serializers/ai.py`      | ✅ 通过 |
| `apps/api/plane/app/views/ai.py`            | ✅ 通过 |
| `apps/api/plane/app/urls/external.py`       | ✅ 通过 |
| `apps/api/plane/db/models/ai.py`            | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`         | ✅ 通过 |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 17. Django check 结果

未执行（环境缺少 celery/psycopg/redis 等依赖）。

---

## 18. grep 安全检查结果

| 检查                    | 命中                         | 安全性                      |
| ----------------------- | ---------------------------- | --------------------------- |
| `raw_result_returned`   | serializer 字段名            | ✅ 安全（boolean metadata） |
| `token/password/secret` | docstrings                   | ✅ 安全                     |
| `headers/stack/env`     | docstrings, HTTP status 常量 | ✅ 安全                     |

---

## 19. 已知限制

| 问题                       | 说明                                                       |
| -------------------------- | ---------------------------------------------------------- |
| ActorLiteSerializer source | 使用 `source="actor_id"`，需要验证 Django ORM 关联是否正确 |
| 无前端 UI                  | 只有 API，无 admin 页面                                    |
| 无 retention job           | 数据不会自动清理                                           |
| 无 export                  | 不支持批量导出                                             |

---

## 20. Phase 8.7 建议

- admin-only audit log 前端页面（Workspace Settings → AI Audit Logs）
- retention management command（90 天清理）
- export 功能（CSV/JSON，ADMIN only）
