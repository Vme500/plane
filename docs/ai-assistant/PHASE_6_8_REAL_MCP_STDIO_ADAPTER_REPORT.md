# 第 6.8 阶段报告：Real MCP stdio Adapter Prototype

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile/typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                          |
| ---------- | ----------------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                      |
| 基于       | `678ce48b8e` — `docs: research real MCP server integration` |
| 工作区状态 | 干净（无未提交修改）                                        |

---

## 2. 是否实现真实 stdio adapter

**是。** 新增 `mcp_stdio_adapter.py`，通过 subprocess 启动 `uvx plane-mcp-server stdio`，使用 MCP JSON-RPC 协议通信。

---

## 3. 是否实际调用 plane-mcp-server

**有条件地是。** 当 `AI_MCP_ADAPTER=stdio` 且 `PLANE_API_KEY` + `PLANE_WORKSPACE_SLUG` 环境变量已设置时，会实际调用 plane-mcp-server。

默认 `AI_MCP_ADAPTER=mock`，不会调用。

---

## 4. adapter 默认值

| 配置                            | 默认值                   | 说明                        |
| ------------------------------- | ------------------------ | --------------------------- |
| `AI_MCP_ADAPTER`                | `mock`                   | 使用 mock/direct DB adapter |
| `AI_MCP_SERVER_COMMAND`         | `uvx`                    | MCP server 启动命令         |
| `AI_MCP_SERVER_ARGS`            | `plane-mcp-server stdio` | 命令参数                    |
| `AI_MCP_SERVER_TIMEOUT_SECONDS` | `15`                     | 请求超时                    |

---

## 5. 新增配置项

| 变量名                          | 读取方式        | 是否返回前端 |
| ------------------------------- | --------------- | ------------ |
| `AI_MCP_ADAPTER`                | `os.environ`    | 否           |
| `AI_MCP_SERVER_COMMAND`         | `os.environ`    | 否           |
| `AI_MCP_SERVER_ARGS`            | `os.environ`    | 否           |
| `AI_MCP_SERVER_TIMEOUT_SECONDS` | `os.environ`    | 否           |
| `PLANE_API_KEY`                 | MCP server 读取 | 否           |
| `PLANE_WORKSPACE_SLUG`          | MCP server 读取 | 否           |

所有配置均从环境变量读取，不需要 migration，不返回前端。

---

## 6. 是否保留 mock adapter

**是。** `AI_MCP_ADAPTER=mock`（默认）时使用 Phase 6.6 的 mock/direct DB adapter。

---

## 7. 是否自动 fallback

**否。** 如果 stdio adapter 失败，返回安全错误，不自动退回 mock。避免用户误以为数据来自 MCP server。

---

## 8. read-only 工具白名单

与 Phase 6 一致：

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

白名单在 `mcp_tools.py` 和 `mcp_stdio_adapter.py` 中双重检查。

---

## 9. 工具名映射

```python
LOCAL_TO_MCP_TOOL = {
    "get_me": "get_me",
    "list_projects": "list_projects",
    "retrieve_project": "retrieve_project",
    "list_work_items": "list_work_items",
    "search_work_items": "search_work_items",
    "retrieve_work_item": "retrieve_work_item",
    "list_states": "list_states",
    "list_labels": "list_labels",
    "list_cycles": "list_cycles",
    "list_modules": "list_modules",
}
```

当前 plane-mcp-server 工具名与本地工具名完全一致，无需重映射。

---

## 10. 写操作硬拒绝

| 检查项                      | 结果                                                           |
| --------------------------- | -------------------------------------------------------------- |
| 白名单外工具拒绝            | ✅ `is_tool_allowed()` 双重检查                                |
| `PROHIBITED_PATTERNS` 列表  | ✅ create/update/delete/assign/move/archive/bulk/import/upload |
| stdio adapter 层再次检查    | ✅ `call_tool_stdio()` 入口检查                                |
| MCP server 工具名不在白名单 | ✅ 拒绝                                                        |

---

## 11. subprocess 安全措施

| 措施                 | 实现                                           |
| -------------------- | ---------------------------------------------- |
| shell=False          | ✅ `subprocess.Popen([command, *args], ...)`   |
| list args            | ✅ 命令和参数分开传递                          |
| 不把 prompt 拼入命令 | ✅ prompt 不传给 subprocess                    |
| timeout              | ✅ `AI_MCP_SERVER_TIMEOUT_SECONDS`（默认 15s） |
| 进程清理             | ✅ terminate → wait → kill → wait              |
| stderr 捕获不返回    | ✅ `stderr=subprocess.PIPE`，不传给调用者      |
| start_new_session    | ✅ 独立进程组                                  |

---

## 12. timeout

默认 15 秒，可通过 `AI_MCP_SERVER_TIMEOUT_SECONDS` 环境变量配置。

覆盖 MCP session 整个生命周期：initialize → tools/call → response。

---

## 13. 错误脱敏

所有 stdio adapter 错误返回统一消息：`"MCP stdio adapter error."`

不暴露：

- subprocess stderr 原文
- 环境变量值
- 文件路径
- 堆栈跟踪
- MCP server 内部错误详情

---

## 14. per-user permission 风险

**stdio adapter 使用 `PLANE_API_KEY`（workspace 级），不能代表当前用户。**

| 维度           | mock adapter | stdio adapter |
| -------------- | ------------ | ------------- |
| 认证           | request.user | PLANE_API_KEY |
| 用户级权限     | ✅ 有        | ❌ 无         |
| workspace 隔离 | ✅ 有        | ✅ 有         |
| project 隔离   | ✅ 有        | ❌ 无         |

---

## 15. 是否做后置权限过滤

**Phase 6.8 未实现后置过滤。** 原因：

1. plane-mcp-server 返回的数据格式是结构化 JSON 对象，字段名可能与本地 model 不同
2. 可靠地提取 project_id 并做 ProjectMember 检查需要对每种工具的返回格式做适配
3. 实现成本高，且可能引入新的解析错误

**替代方案**：stdio adapter 默认关闭（`AI_MCP_ADAPTER=mock`），只有管理员明确启用时才使用。

---

## 16. 哪些结果不允许返回

在未实现后置过滤的情况下，stdio adapter 的结果**不应被视为用户权限范围内的数据**。

使用 stdio adapter 时，管理员应知晓：

- 返回的数据可能包含当前用户无权访问的 project 数据
- 这是 workspace API key 的固有限制
- 后续阶段可通过 OAuth + HTTP transport 实现 per-user 权限

---

## 17. 是否新增 migration

**否。**

---

## 18. 是否修改 Docker

**否。**

---

## 19. 是否实现写操作

**否。** 只允许 read-only 工具。

---

## 20. 是否实现 Claude Code Runtime

**否。**

---

## 21. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_stdio_adapter.py`    | ✅ 通过 |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 22. typecheck/lint 结果

| 检查      | 结果    | 备注                   |
| --------- | ------- | ---------------------- |
| typecheck | ✅ 通过 | exit 0                 |
| lint      | ✅ 通过 | 0 errors, 997 warnings |

---

## 23. 已知问题

| 问题                   | 说明                               | 后续方案                    |
| ---------------------- | ---------------------------------- | --------------------------- |
| 无后置权限过滤         | stdio 返回数据可能超出用户权限     | Phase 6.9 或后续阶段实现    |
| 每次请求启动新进程     | 性能开销                           | Phase 6.9 可考虑连接池      |
| MCP SDK 未安装         | 使用原生 JSON-RPC over subprocess  | 如需更完整功能可安装 mcp 包 |
| `select` 模块读 stdout | 同步阻塞，适合 Django 请求生命周期 | 可用 asyncio 优化           |

---

## 24. 是否可以进入 Phase 6.9 安全验证

**是。** stdio adapter prototype 已完成，可以进行安全验证。

---

## 25. 是否可以进入写操作阶段

**否。** 建议先完成 stdio adapter 安全验证和后置权限过滤，再考虑写操作。

---

## 修改文件清单

| 文件                                     | 变更                                                |
| ---------------------------------------- | --------------------------------------------------- |
| `apps/api/plane/ai/mcp_stdio_adapter.py` | 新增：stdio MCP adapter（JSON-RPC over subprocess） |
| `apps/api/plane/ai/mcp_runtime.py`       | 修改：添加 adapter dispatch（mock/stdio）           |

---

## 26. Phase 6.9 修复记录（2026-05-28）

Phase 6.8 的"未实现后置权限过滤"问题已在 Phase 6.9 中修复，详见 [`PHASE_6_9_MCP_STDIO_SAFETY_VALIDATION_REPORT.md`](./PHASE_6_9_MCP_STDIO_SAFETY_VALIDATION_REPORT.md)。

**修复内容**：

- `get_me`：pass-through（安全）
- `list_projects`：与 accessible projects 交叉过滤
- `retrieve_project`：预验证 project access
- 其他 7 个工具：阻断，返回 clear error
- 所有 stdio 结果必须经过 `_filter_stdio_result()` 才返回前端
