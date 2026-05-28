# 第 6.6 阶段报告：Harden Read-Only MCP Runtime Permissions

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：修复完成，typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                             |
| ---------- | -------------------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                         |
| 基于       | `f205cacc59` — `docs: validate read-only MCP runtime security` |
| 工作区状态 | 干净（无未提交修改）                                           |

---

## 2. 修复前的权限问题

Phase 6.5 安全审查发现以下问题：

| #   | 问题                                                                                        | 严重性 |
| --- | ------------------------------------------------------------------------------------------- | ------ |
| 1   | `retrieve_project` 不验证 workspace 归属                                                    | 高     |
| 2   | `list_work_items` / `search_work_items` 不验证 workspace                                    | 高     |
| 3   | `retrieve_work_item` 不验证 workspace                                                       | 高     |
| 4   | 所有 project 级工具不检查 project membership                                                | 高     |
| 5   | `list_projects` 缺少 `deleted_at` 过滤                                                      | 中     |
| 6   | Issue 工具使用 `Issue.objects` 而非 `Issue.issue_objects`                                   | 中     |
| 7   | `list_states` / `list_labels` / `list_cycles` / `list_modules` 无 archived 过滤             | 中     |
| 8   | `list_projects` / `list_states` / `list_labels` / `list_cycles` / `list_modules` 无数量限制 | 中     |
| 9   | 错误消息泄露异常详情                                                                        | 低     |

---

## 3. 修复了哪些工具

全部 10 个工具均已修复：

| 工具                 | 修复内容                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| `get_me`             | 不再返回 "message" 字段，只返回 user_id                                                        |
| `list_projects`      | 添加 workspace member 校验、membership/public network 过滤、数量限制                           |
| `retrieve_project`   | 添加 workspace + project access 校验                                                           |
| `list_work_items`    | 改用 `Issue.issue_objects`、添加 project membership 校验、workspace 校验、数量限制             |
| `search_work_items`  | 改用 `Issue.issue_objects`、添加 project membership 校验、query 长度限制 200 字符、数量限制    |
| `retrieve_work_item` | 改用 `Issue.issue_objects`、添加 workspace + project membership 校验                           |
| `list_states`        | 添加 project membership 校验、`is_triage=False`、`project__archived_at__isnull=True`、数量限制 |
| `list_labels`        | 添加 project membership 校验、`project__archived_at__isnull=True`、数量限制                    |
| `list_cycles`        | 添加 project membership 校验、`archived_at__isnull=True`、数量限制                             |
| `list_modules`       | 添加 project membership 校验、`archived_at__isnull=True`、数量限制                             |

---

## 4. workspace 校验如何实现

**方式**：`_require_workspace_member(user, workspace_slug)` helper。

```python
WorkspaceMember.objects.select_related("workspace").get(
    workspace__slug=workspace_slug,
    member=user,
    is_active=True,
)
```

- 确认当前 user 是 workspace 的 active member
- 非成员返回 `PERMISSION_DENIED_ERROR`
- 防御纵深：endpoint 的 `@allow_permission` 装饰器已做第一层校验

---

## 5. project membership 校验如何实现

**两层校验**：

### 5.1 ProjectBasePermission 级（list_projects / retrieve_project）

使用 `_get_accessible_projects_qs()`：

```python
Project.objects.filter(
    workspace__slug=workspace_slug,
).filter(
    Q(project_projectmember__member=user, project_projectmember__is_active=True)
    | Q(network=2)  # Public projects
)
```

与 Plane 现有 `ProjectListCreateAPIEndpoint.get_queryset()` 完全一致。

### 5.2 ProjectEntityPermission 级（所有 entity 工具）

使用 `_get_project_or_none()`：

```python
Project.objects.filter(
    workspace__slug=workspace_slug,
    pk=project_id,
    project_projectmember__member=user,
    project_projectmember__is_active=True,
).get()
```

与 Plane 现有 State/Label/Cycle/Module/Issue list API 的 membership 过滤一致。

---

## 6. soft-deleted 过滤如何实现

**方式**：依赖 Plane 的 `SoftDeletionManager`。

- `Project.objects` / `Issue.issue_objects` / `State.objects` 等都继承了 `SoftDeletionManager`
- 该 manager 自动在 `get_queryset()` 中添加 `deleted_at__isnull=True`
- 不需要手动添加 `deleted_at` 过滤
- 与 Plane 现有 API 行为一致

---

## 7. archived 过滤如何实现

按照 Plane 现有 API 的模式，不同实体有不同的 archived 处理方式：

| 实体    | 过滤方式                                                            | 对应 Plane API               |
| ------- | ------------------------------------------------------------------- | ---------------------------- |
| Project | 不在 list queryset 中过滤 archived                                  | ProjectListCreateAPIEndpoint |
| Issue   | `Issue.issue_objects` 自动排除 `archived_at__isnull=False`          | IssueManager                 |
| Issue   | `Issue.issue_objects` 自动排除 `project__archived_at__isnull=False` | IssueManager                 |
| State   | `.filter(project__archived_at__isnull=True)`                        | StateListAPIEndpoint         |
| Label   | `.filter(project__archived_at__isnull=True)`                        | LabelListAPIEndpoint         |
| Cycle   | `.filter(archived_at__isnull=True)`                                 | CycleListAPIEndpoint.get()   |
| Module  | `.filter(archived_at__isnull=True)`                                 | ModuleListAPIEndpoint.get()  |

---

## 8. 返回字段白名单

| 工具               | 返回字段                                       |
| ------------------ | ---------------------------------------------- |
| get_me             | user_id                                        |
| list_projects      | id, name, identifier, description              |
| retrieve_project   | id, name, identifier, description              |
| list_work_items    | id, name, state\_\_name, priority              |
| search_work_items  | id, name, state\_\_name, priority              |
| retrieve_work_item | id, name, description, state, priority         |
| list_states        | id, name, group, color                         |
| list_labels        | id, name, color                                |
| list_cycles        | id, name, start_date, end_date                 |
| list_modules       | id, name, description, start_date, target_date |

所有字段通过 `.values()` 指定，不返回完整 model `__dict__`。

---

## 9. list/search limit

| 工具              | 默认限制 | 最大限制 |
| ----------------- | -------- | -------- |
| list_projects     | 20       | 50       |
| list_work_items   | 20       | 50       |
| search_work_items | 20       | 20       |
| list_states       | 20       | 50       |
| list_labels       | 20       | 50       |
| list_cycles       | 20       | 50       |
| list_modules      | 20       | 50       |

`safe_limit()` 函数确保所有限制在 `[1, MAX_LIMIT]` 范围内。search_work_items 的 query 长度限制为 200 字符。

---

## 10. 写操作硬拒绝检查

| 检查项                      | 结果 | 说明                       |
| --------------------------- | ---- | -------------------------- |
| 白名单外工具拒绝            | ✅   | `is_tool_allowed()` 检查   |
| create/update/delete 等拒绝 | ✅   | `PROHIBITED_PATTERNS` 列表 |
| 不会自动执行任意函数        | ✅   | 只调用预定义函数           |
| 没有 getattr 动态调用       | ✅   | 使用 if/elif 分支          |
| 没有 eval/exec              | ✅   | 无动态代码执行             |
| 没有 subprocess             | ✅   | 无子进程调用               |
| 没有 shell=True             | ✅   | 无命令执行                 |
| 没有用户 prompt 拼进命令    | ✅   | 无命令拼接                 |

---

## 11. 是否仍是 mock/direct DB adapter

**是。** 仍然直接查询 Plane 数据库，未调用真实 MCP server。

---

## 12. 是否真实调用 plane-mcp-server

**否。**

---

## 13. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 14. typecheck/lint 结果

| 检查      | 结果    | 备注                   |
| --------- | ------- | ---------------------- |
| typecheck | ✅ 通过 | exit 0                 |
| lint      | ✅ 通过 | 0 errors, 997 warnings |

---

## 15. 是否新增 migration

**否。**

---

## 16. 是否修改 Docker

**否。**

---

## 17. 是否实现写操作

**否。** 只修复 read-only 工具的权限问题。

---

## 18. 已知剩余风险

| 风险                | 说明                                      | 缓解               |
| ------------------- | ----------------------------------------- | ------------------ |
| Intent 解析简单     | 使用关键词匹配，不是 LLM function calling | 后续阶段优化       |
| 无审计日志          | 不记录 MCP 工具调用                       | Phase 8 计划       |
| 异常消息脱敏        | 当前返回通用 "Access denied" 消息         | 已实现 fail-closed |
| 未接真实 MCP server | 当前是 mock adapter                       | 后续阶段集成       |

---

## 19. 是否可以进入真实 MCP Server 集成调研

**是。** 权限问题已修复，可以安全地进入 MCP server 集成调研阶段。

---

## 20. 是否可以进入写操作阶段

**是，但建议先集成真实 MCP server。** 写操作需要更严格的安全机制（确认对话框、审计日志），建议在真实 MCP server 集成后再考虑。

---

## 修改文件清单

| 文件                                        | 变更                                                                                    |
| ------------------------------------------- | --------------------------------------------------------------------------------------- |
| `apps/api/plane/ai/mcp_tools.py`            | 重写：添加安全 helper、workspace 校验、project membership 校验、archived 过滤、数量限制 |
| `apps/api/plane/ai/mcp_runtime.py`          | 修改：`user_id` 参数改为 `user` 对象                                                    |
| `apps/api/plane/app/views/external/base.py` | 修改：传递 `request.user` 而非 `user_id` 字符串                                         |
