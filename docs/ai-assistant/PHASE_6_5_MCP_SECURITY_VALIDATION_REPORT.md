# 第 6.5 阶段报告：MCP Read-only Runtime 安全审查

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：审查完成，发现权限问题需修复

---

## 1. 当前分支和 commit

| 项目        | 值                                                        |
| ----------- | --------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                    |
| 最新 commit | `bb916a7e43` — `feat: add read-only MCP runtime skeleton` |
| 工作区状态  | 干净（无未提交修改）                                      |

---

## 2. 当前实现是否真实调用 plane-mcp-server

**否。** 当前实现是 **MCP-compatible read-only runtime skeleton / mock adapter**。

- 没有调用 plane-mcp-server
- 没有使用 MCP SDK
- 直接查询 Plane 数据库作为 mock 实现
- 真实 MCP Server 集成需后续单独阶段完成

---

## 3. 每个 read-only 工具的权限审查结果

### 3.1 get_me

| 检查项              | 结果 | 说明               |
| ------------------- | ---- | ------------------ |
| 限定 workspace slug | ✅   | 只返回当前 user_id |
| 使用 request.user   | ✅   | 从 endpoint 传入   |
| 过滤 soft-deleted   | N/A  | 不查询数据库       |
| 限制返回数量        | N/A  | 单条数据           |
| 安全字段            | ✅   | 只返回 user_id     |

### 3.2 list_projects

| 检查项                  | 结果 | 说明                                         |
| ----------------------- | ---- | -------------------------------------------- |
| 限定 workspace slug     | ✅   | `Workspace.objects.get(slug=workspace_slug)` |
| 过滤 soft-deleted       | ❌   | **缺少** `deleted_at__isnull=True`           |
| 过滤 archived           | ❌   | **缺少** `archived_at__isnull=True`          |
| 检查 project membership | ❌   | **缺少** 项目成员检查                        |
| 限制返回数量            | ❌   | **缺少** 数量限制                            |
| 安全字段                | ✅   | 只返回 id, name, identifier, description     |

### 3.3 retrieve_project

| 检查项                  | 结果 | 说明                                     |
| ----------------------- | ---- | ---------------------------------------- |
| 限定 workspace slug     | ❌   | **缺少** workspace 验证                  |
| 过滤 soft-deleted       | ❌   | **缺少** `deleted_at__isnull=True`       |
| 检查 project membership | ❌   | **缺少** 项目成员检查                    |
| 安全字段                | ✅   | 只返回 id, name, identifier, description |

### 3.4 list_work_items / search_work_items

| 检查项                  | 结果 | 说明                                         |
| ----------------------- | ---- | -------------------------------------------- |
| 限定 workspace slug     | ❌   | **缺少** workspace 验证                      |
| 过滤 archived           | ❌   | **缺少** `archived_at__isnull=True`          |
| 过滤 project archived   | ❌   | **缺少** `project__archived_at__isnull=True` |
| 检查 project membership | ❌   | **缺少** 项目成员检查                        |
| 限制返回数量            | ✅   | 限制 50/20 条                                |
| 安全字段                | ✅   | 只返回 id, name, state\_\_name, priority     |

### 3.5 retrieve_work_item

| 检查项                  | 结果 | 说明                                          |
| ----------------------- | ---- | --------------------------------------------- |
| 限定 workspace slug     | ❌   | **缺少** workspace 验证                       |
| 过滤 archived           | ❌   | **缺少** `archived_at__isnull=True`           |
| 检查 project membership | ❌   | **缺少** 项目成员检查                         |
| 安全字段                | ✅   | 只返回 id, name, description, state, priority |

### 3.6 list_states / list_labels / list_cycles / list_modules

| 检查项                  | 结果 | 说明                    |
| ----------------------- | ---- | ----------------------- |
| 限定 workspace slug     | ❌   | **缺少** workspace 验证 |
| 检查 project membership | ❌   | **缺少** 项目成员检查   |
| 限制返回数量            | ❌   | **缺少** 数量限制       |
| 安全字段                | ✅   | 只返回安全字段          |

---

## 4. 是否存在跨 workspace 数据风险

**是。** 风险点：

1. `retrieve_project` 不验证 project 是否属于当前 workspace
2. `list_work_items` / `search_work_items` 不验证 project 是否属于当前 workspace
3. `retrieve_work_item` 不验证 issue 是否属于当前 workspace
4. `list_states` / `list_labels` / `list_cycles` / `list_modules` 不验证 project 是否属于当前 workspace

**攻击场景**：用户可以通过指定其他 workspace 的 project_id 来访问跨 workspace 数据。

---

## 5. 是否存在 project 权限绕过风险

**是。** 风险点：

1. 所有 project 级工具都不检查当前用户是否是 project member
2. 即使用户不是 project member，也可以通过 project_id 访问项目数据
3. 这绕过了 Plane 的 project membership 权限控制

---

## 6. 是否过滤 soft-deleted 数据

**否。** 风险点：

1. `list_projects` 不过滤 `deleted_at__isnull=True`
2. `retrieve_project` 不过滤 `deleted_at__isnull=True`
3. Issue 相关工具不过滤 `archived_at__isnull=True`

---

## 7. 是否限制返回数量

**部分。**

| 工具              | 限制      |
| ----------------- | --------- |
| list_projects     | ❌ 无限制 |
| list_work_items   | ✅ 50 条  |
| search_work_items | ✅ 20 条  |
| list_states       | ❌ 无限制 |
| list_labels       | ❌ 无限制 |
| list_cycles       | ❌ 无限制 |
| list_modules      | ❌ 无限制 |

---

## 8. 是否只返回安全字段

**是。** 所有工具都使用 `.values()` 指定返回字段，不返回完整 model `__dict__`。

---

## 9. 写操作硬拒绝检查结果

| 检查项                      | 结果 | 说明                       |
| --------------------------- | ---- | -------------------------- |
| 白名单之外的工具拒绝        | ✅   | `is_tool_allowed()` 检查   |
| create/update/delete 等拒绝 | ✅   | `PROHIBITED_PATTERNS` 列表 |
| 不会自动执行任意函数        | ✅   | 只调用预定义的 mock 函数   |
| 没有 getattr 动态调用       | ✅   | 使用 if/elif 分支          |
| 没有 eval/exec              | ✅   | 无动态代码执行             |
| 没有 shell=True             | ✅   | 无 subprocess 调用         |
| 没有用户 prompt 拼进命令    | ✅   | 无命令执行                 |

---

## 10. endpoint mode=mcp 安全检查结果

| 检查项                                 | 结果 | 说明                                      |
| -------------------------------------- | ---- | ----------------------------------------- |
| mode 默认为 standard                   | ✅   | `request.data.get("mode", "standard")`    |
| mode!=mcp 时原行为不变                 | ✅   | 只在 `mode == "mcp"` 时进入 MCP path      |
| mode==mcp 时检查 ENABLE_AI_MCP_RUNTIME | ✅   | `is_mcp_runtime_enabled()` 检查           |
| enable_ai_mcp_runtime=false 时返回错误 | ✅   | 返回 "MCP runtime is not enabled"         |
| 权限 WORKSPACE ADMIN/MEMBER            | ✅   | `@allow_permission` 装饰器                |
| GUEST 不能访问                         | ✅   | `allowed_roles=[ROLE.ADMIN, ROLE.MEMBER]` |
| 错误不泄露 stack/secret                | ✅   | 只返回错误消息                            |

---

## 11. 前端 MCP mode 安全检查结果

| 检查项                                          | 结果 | 说明                             |
| ----------------------------------------------- | ---- | -------------------------------- |
| MCP mode 只在 enable_ai_mcp_runtime=true 时显示 | ✅   | 条件渲染                         |
| 默认 Standard Chat                              | ✅   | `useState<ChatMode>("standard")` |
| payload 正确                                    | ✅   | `payload.mode = "mcp"`           |
| 不直接 JSON.stringify 完整对象                  | ✅   | 使用 `extractMCPToolSummary()`   |
| 不展示 headers/config/request/stack             | ✅   | 只展示摘要                       |
| 不展示 token/API key/cookie/password            | ✅   | 无敏感信息                       |
| 工具结果摘要可读                                | ✅   | 格式化展示                       |
| 错误信息脱敏                                    | ✅   | 只展示错误消息                   |
| 不影响 standard prompt-response                 | ✅   | 独立 mode 处理                   |

---

## 12. 是否做了小修复

**否。** 权限问题较多，需要较大改动。记录在报告中，后续修复。

---

## 13. Python py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/__init__.py`             | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 14. typecheck/lint 结果

| 检查      | 结果    | 备注                   |
| --------- | ------- | ---------------------- |
| typecheck | ✅ 通过 | Phase 6 已验证         |
| lint      | ✅ 通过 | 0 errors, 997 warnings |

---

## 15. 是否新增 migration

**否。**

---

## 16. 是否修改 Docker

**否。**

---

## 17. 是否实现写操作

**否。** 只实现 read-only 工具。

---

## 18. 是否实现 Claude Code Runtime

**否。**

---

## 19. 是否可以进入真实 MCP Server 集成

**是，但需先修复权限问题。** 当前 mock 实现有权限风险，需先修复后再集成真实 MCP Server。

---

## 20. 是否可以进入写操作确认阶段

**否。** 需先修复 read-only 工具的权限问题，再考虑写操作。

---

## 21. 修复建议

### 高优先级（必须修复）

1. **添加 workspace 验证**：所有 project 级工具必须验证 project 属于当前 workspace
2. **添加 soft-deleted 过滤**：所有查询必须添加 `deleted_at__isnull=True` 和 `archived_at__isnull=True`
3. **添加 project membership 检查**：验证当前用户是 project member

### 中优先级

4. **添加返回数量限制**：list_projects, list_states, list_labels, list_cycles, list_modules 添加 LIMIT
5. **使用 ProjectMember 模型**：检查 `ProjectMember.objects.filter(project=project, member=request.user, is_active=True)`

### 低优先级

6. **异常脱敏**：不要返回完整异常信息，只返回安全的错误消息
7. **审计日志**：记录所有 MCP 工具调用

---

## 22. 总结

| 类别             | 状态         | 说明                             |
| ---------------- | ------------ | -------------------------------- |
| 实现类型         | Mock adapter | 不是真实 MCP server 调用         |
| 写操作拒绝       | ✅ 安全      | 白名单 + 禁止模式                |
| workspace 隔离   | ❌ 有风险    | 部分工具缺少 workspace 验证      |
| project 权限     | ❌ 有风险    | 缺少 project membership 检查     |
| soft-delete 过滤 | ❌ 有风险    | 缺少 deleted_at/archived_at 过滤 |
| 返回数量限制     | ⚠️ 部分      | 部分工具无限制                   |
| 安全字段         | ✅ 安全      | 使用 .values() 指定字段          |
| endpoint 安全    | ✅ 安全      | 权限装饰器正确                   |
| 前端安全         | ✅ 安全      | 不展示敏感信息                   |

---

## 23. Phase 6.6 修复记录（2026-05-28）

以上安全问题已在 Phase 6.6 中全部修复，详见 [`PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md`](./PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md)。

**修复状态**：

| 类别             | 修复前    | 修复后                           |
| ---------------- | --------- | -------------------------------- |
| workspace 隔离   | ❌ 有风险 | ✅ 已修复                        |
| project 权限     | ❌ 有风险 | ✅ 已修复                        |
| soft-delete 过滤 | ❌ 有风险 | ✅ 已修复（SoftDeletionManager） |
| archived 过滤    | ❌ 有风险 | ✅ 已修复（按 Plane API 模式）   |
| 返回数量限制     | ⚠️ 部分   | ✅ 已修复（全部有限制）          |
