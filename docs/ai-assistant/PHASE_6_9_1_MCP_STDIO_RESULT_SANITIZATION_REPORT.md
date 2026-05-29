# 第 6.9.1 阶段报告：Sanitize MCP stdio Adapter Results

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile/typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                                 |
| ---------- | ------------------------------------------------------------------ |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                             |
| 基于       | `a9fe2b914a` — `fix: gate MCP stdio adapter results by permission` |
| 工作区状态 | 干净（无未提交修改）                                               |

---

## 2. Phase 6.9 遗留问题

Phase 6.9 的安全闸门存在以下数据净化问题：

1. `get_me` 仍然 pass-through MCP raw result（MCP server 返回的是 API key owner，不是 request.user）
2. `list_projects` 从 MCP raw result 提取字段（可能包含额外字段）
3. MCP raw result 的字段可能超出安全白名单

---

## 3. get_me 如何修复

**修复前**：`return {"success": True, "result": raw_result}` — 直接返回 MCP server 的 get_me 结果（API key owner 身份）。

**修复后**：`return {"success": True, "result": _serialize_user_safe(user)}` — 基于 request.user 生成安全响应。

`_serialize_user_safe(user)` 只返回：

- `id` — user UUID
- `display_name` — first_name + last_name（如有）
- `email` — email（如有）

不返回：password, token, session, auth provider internals, API key owner info。

---

## 4. list_projects 如何净化

**修复前**：从 MCP raw result 提取 `proj.get("id")`, `proj.get("name")` 等字段。

**修复后**：完全忽略 MCP result，直接查询本地 DB：

```python
projects = _get_accessible_projects_qs(user, workspace_slug).values(
    "id", "name", "identifier", "description"
)[:50]
```

与 mock adapter 使用相同的 queryset 和字段白名单。

---

## 5. retrieve_project 如何净化

Phase 6.9 已正确实现：使用 `_get_accessible_project_or_none()` 从本地 DB 返回安全字段。无需修改。

---

## 6. raw MCP result 是否还会返回前端

**否。** 所有三个允许的 stdio 工具现在都使用本地 DB 数据或 request.user 数据，不使用 MCP raw result。

---

## 7. 哪些 stdio tools 允许

| 工具               | 数据来源                                     |
| ------------------ | -------------------------------------------- |
| `get_me`           | request.user（`_serialize_user_safe`）       |
| `list_projects`    | 本地 DB（`_get_accessible_projects_qs`）     |
| `retrieve_project` | 本地 DB（`_get_accessible_project_or_none`） |

---

## 8. 哪些 stdio tools 继续拒绝

`list_work_items`、`search_work_items`、`retrieve_work_item`、`list_states`、`list_labels`、`list_cycles`、`list_modules`。

---

## 9. 是否保留 mock adapter

**是。**

---

## 10. 是否自动 fallback

**否。**

---

## 11. 是否新增 migration

**否。**

---

## 12. 是否修改 Docker

**否。**

---

## 13. 是否实现写操作

**否。**

---

## 14. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_stdio_adapter.py`    | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 15. typecheck/lint 结果

| 检查      | 结果                |
| --------- | ------------------- |
| typecheck | ✅ 通过             |
| lint      | ✅ 通过（0 errors） |

---

## 16. 是否可以 push

**是。**

---

## 17. 是否可以进入 Phase 7

**建议先 push 备份。**

---

## 18. 是否可以进入写操作阶段

**否。**

---

## 修改文件清单

| 文件                               | 变更                                                                                                                                         |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/plane/ai/mcp_runtime.py` | 新增 `_serialize_user_safe()`；重写 `get_me` 和 `list_projects` 的 `_filter_stdio_result` 逻辑；更新 `format_mcp_response_text` 兼容新旧格式 |

---

## 19. Phase 7 实施记录（2026-05-28）

Phase 7 实现了 MCP Tool Preview UI，详见 [`PHASE_7_MCP_TOOL_PREVIEW_UI_REPORT.md`](./PHASE_7_MCP_TOOL_PREVIEW_UI_REPORT.md)。

**关键变化**：

- `mcp_result` 已从 endpoint 响应中移除
- 新增 `mcp_preview` 结构化字段
- 前端渲染 MCP Tool Preview 区块
