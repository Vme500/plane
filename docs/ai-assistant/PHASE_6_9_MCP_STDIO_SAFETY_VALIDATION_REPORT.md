# 第 6.9 阶段报告：MCP stdio Adapter Safety Gate

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile/typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                          |
| ---------- | ----------------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                      |
| 基于       | `f75ffbad46` — `feat: add real MCP stdio adapter prototype` |
| 工作区状态 | 干净（无未提交修改）                                        |

---

## 2. Phase 6.8 遗留权限风险

Phase 6.8 的 stdio adapter 将 MCP server 返回的数据**原样传给前端**，未做任何用户权限过滤。由于 `PLANE_API_KEY` 是 workspace 级 API key，MCP server 可以返回当前用户无权访问的 project 数据。

---

## 3. 是否真实调用 plane-mcp-server

有条件地是。当 `AI_MCP_ADAPTER=stdio` 且环境变量已设置时，会调用。但经过 Phase 6.9 安全闸门后，只有 3 个工具允许通过。

---

## 4. stdio adapter 是否默认启用

**否。** 默认 `AI_MCP_ADAPTER=mock`。

---

## 5. mock adapter 是否保留

**是。** 默认使用 Phase 6.6 权限加固版 mock adapter。

---

## 6. 是否允许未经后置过滤的 stdio result 返回前端

**否。** Phase 6.9 实现了安全闸门，所有 stdio 结果必须经过 `_filter_stdio_result()` 后置过滤。

---

## 7. 选择了方案 A/B/C 中哪一个

**方案 A 最小子集 + 方案 B fallback。**

具体实现：

| 工具               | 策略                   | 说明                                                                    |
| ------------------ | ---------------------- | ----------------------------------------------------------------------- |
| `get_me`           | ✅ 方案 A pass-through | 无 workspace/project 数据，安全                                         |
| `list_projects`    | ✅ 方案 A 后置过滤     | 从 MCP 结果中提取 project ID，与用户 accessible projects 交叉过滤       |
| `retrieve_project` | ✅ 方案 A 后置验证     | 验证 project_id 属于用户可访问范围                                      |
| 其他 7 个工具      | ❌ 方案 B 阻断         | 返回 "not available until per-user permission filtering is implemented" |

---

## 8. 哪些 stdio tools 允许

| 工具               | 方式                                       |
| ------------------ | ------------------------------------------ |
| `get_me`           | pass-through（无敏感数据）                 |
| `list_projects`    | post-filter（与 accessible projects 交叉） |
| `retrieve_project` | pre-validate（检查 project access）        |

---

## 9. 哪些 stdio tools 拒绝

| 工具                 | 原因                               |
| -------------------- | ---------------------------------- |
| `list_work_items`    | 无法可靠提取 project_id 做后置过滤 |
| `search_work_items`  | 无法可靠提取 project_id 做后置过滤 |
| `retrieve_work_item` | 无法可靠提取 project_id 做后置过滤 |
| `list_states`        | 无 project_id 参数，无法验证       |
| `list_labels`        | 无 project_id 参数，无法验证       |
| `list_cycles`        | 无 project_id 参数，无法验证       |
| `list_modules`       | 无 project_id 参数，无法验证       |

---

## 10. 后置权限过滤如何实现

新增 `_filter_stdio_result()` 函数：

```python
def _filter_stdio_result(user, workspace_slug, tool_name, raw_result, arguments):
```

**get_me**：直接 pass-through。

**list_projects**：

1. 从 MCP 结果（JSON array）中提取每个 project 的 `id`
2. 查询 `_get_accessible_projects_qs(user, workspace_slug)` 获取用户可访问的 project ID 集合
3. 只返回交集中的 project
4. 只返回安全字段：id, name, identifier, description

**retrieve_project**：

1. 从 arguments 或 MCP 结果中提取 `project_id`
2. 调用 `_get_accessible_project_or_none(user, workspace_slug, project_id)` 验证
3. 无权限时返回 `PERMISSION_DENIED_ERROR`
4. 有权限时从本地 DB 返回安全字段（不使用 MCP 返回的原始数据）

**其他工具**：直接返回 `_STDIO_BLOCKED_MSG` 错误。

---

## 11. 无法过滤时如何 fail closed

- `_filter_stdio_result()` 的所有异常路径都返回 `PERMISSION_DENIED_ERROR`
- `_uuid_eq()` 的异常被捕获并返回 False（拒绝）
- MCP 结果格式不符预期时返回 `PERMISSION_DENIED_ERROR`
- 不暴露 "object exists but you don't have permission"

---

## 12. 是否修复 MEMBER 获取越权数据风险

**是。** Phase 6.9 之前，MEMBER 可以通过 stdio adapter 获取 workspace 下所有 project 数据（包括非 member 的 project）。Phase 6.9 后：

- `list_projects` 只返回 MEMBER 有权限的 project
- `retrieve_project` 验证 MEMBER 有权限才返回
- 其他工具全部阻断

---

## 13. 是否仍存在 workspace API key 权限风险

**是，但已缓解。** `PLANE_API_KEY` 仍然是 workspace 级 API key，但 Phase 6.9 的安全闸门确保：

- 只有经过用户权限过滤的数据才返回前端
- 未过滤的工具被阻断
- 即使 MCP server 返回了越权数据，也不会传给前端

---

## 14. 写操作硬拒绝检查

| 检查项                     | 结果 |
| -------------------------- | ---- |
| 白名单外工具拒绝           | ✅   |
| `PROHIBITED_PATTERNS` 列表 | ✅   |
| stdio adapter 层再次检查   | ✅   |
| 安全闸门层再次检查         | ✅   |

---

## 15. 是否自动 fallback

**否。** stdio 失败返回安全错误，不退回 mock。

---

## 16. 是否新增 migration

**否。**

---

## 17. 是否修改 Docker

**否。**

---

## 18. 是否实现写操作

**否。**

---

## 19. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_stdio_adapter.py`    | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 20. typecheck/lint 结果

| 检查      | 结果    | 备注                   |
| --------- | ------- | ---------------------- |
| typecheck | ✅ 通过 | exit 0                 |
| lint      | ✅ 通过 | 0 errors, 997 warnings |

---

## 21. 已知问题

| 问题                    | 说明               | 后续方案                         |
| ----------------------- | ------------------ | -------------------------------- |
| 7 个工具被阻断          | stdio 模式下不可用 | 实现 per-user OAuth token 后解除 |
| 每次请求启动新进程      | 性能开销           | 后续可用连接池                   |
| list_projects UUID 比较 | 依赖 UUID 格式一致 | 已做异常保护                     |

---

## 22. 是否可以 push

**是。** 安全闸门已实现，可以安全 push。

---

## 23. 是否可以进入 Phase 7

**建议先 push 备份，再评估。** Phase 7 是写操作确认阶段，与 stdio adapter 安全性相关但独立。

---

## 24. 是否可以进入写操作阶段

**否。** 建议先完成 stdio adapter 的 OAuth per-user token 支持，再考虑写操作。

---

## 修改文件清单

| 文件                               | 变更                                                                                                                                    |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/plane/ai/mcp_runtime.py` | 新增 `_filter_stdio_result()`、`_uuid_eq()`、`_STDIO_PASS_THROUGH`、`_STDIO_FILTERABLE`、`_STDIO_BLOCKED_MSG`；更新 stdio dispatch 路径 |

---

## 25. Phase 6.9.1 修复记录（2026-05-28）

Phase 6.9 遗留的数据净化问题已在 Phase 6.9.1 中修复，详见 [`PHASE_6_9_1_MCP_STDIO_RESULT_SANITIZATION_REPORT.md`](./PHASE_6_9_1_MCP_STDIO_RESULT_SANITIZATION_REPORT.md)。

**修复内容**：

- `get_me`：不再 pass-through MCP raw result，改为 `_serialize_user_safe(request.user)`
- `list_projects`：不再从 MCP result 提取字段，改为本地 DB 查询
- MCP raw result 永远不返回前端
