# 第 6.7 阶段报告：Real plane-mcp-server Integration Research

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：调研完成，未修改功能代码

---

## 1. 当前分支和 commit

| 项目        | 值                                                             |
| ----------- | -------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                         |
| 最新 commit | `32cafcc427` — `fix: harden read-only MCP runtime permissions` |
| 工作区状态  | 干净（无未提交修改）                                           |

---

## 2. 当前实现是否真实调用 plane-mcp-server

**否。** 当前实现是 mock/direct DB adapter，直接查询 Plane 数据库。

---

## 3. 当前 mock adapter 状态

Phase 6.6 已修复权限问题：

- ✅ workspace 校验（defense-in-depth）
- ✅ project membership 校验
- ✅ soft-deleted 过滤（SoftDeletionManager）
- ✅ archived 过滤（按 Plane API 模式）
- ✅ 返回数量限制
- ✅ 安全字段白名单
- ✅ 写操作硬拒绝

---

## 4. Python/MCP/uv/uvx 环境检查结果

| 工具             | 状态                  | 版本/路径                          |
| ---------------- | --------------------- | ---------------------------------- |
| python3          | ✅ 可用               | Python 3.14.4 (`/usr/bin/python3`) |
| uv               | ✅ 可用               | `/home/qq402/.local/bin/uv`        |
| uvx              | ✅ 可用               | `/home/qq402/.local/bin/uvx`       |
| plane-mcp-server | ✅ 可通过 uvx 运行    | `uvx plane-mcp-server stdio`       |
| mcp SDK (Python) | ❌ 系统 python 未安装 | plane-mcp-server 环境内可用        |

---

## 5. plane-mcp-server 是否可用

**是。** `uvx plane-mcp-server stdio` 可运行，但需要以下环境变量：

| 变量名                    | 是否必需 | 说明                                              |
| ------------------------- | -------- | ------------------------------------------------- |
| `PLANE_API_KEY`           | ✅ 必需  | Plane workspace API key                           |
| `PLANE_WORKSPACE_SLUG`    | ✅ 必需  | 当前 workspace slug                               |
| `PLANE_BASE_URL`          | 可选     | Plane API base URL（默认 `https://api.plane.so`） |
| `PLANE_INTERNAL_BASE_URL` | 可选     | 内部 API URL（优先于 BASE_URL）                   |

**运行模式**：

| 模式  | 命令                     | 传输                    |
| ----- | ------------------------ | ----------------------- |
| stdio | `plane-mcp-server stdio` | stdin/stdout            |
| http  | `plane-mcp-server http`  | HTTP + SSE（端口 8211） |

**stdio 模式最适合 Phase 6.8 集成**：API 进程通过 subprocess 启动，通过 stdin/stdout 通信。

---

## 6. MCP Transport 方案比较

### 方案 A：API 进程内 Python MCP client + stdio 启动 plane-mcp-server

| 项目           | 说明                                                                                                                    |
| -------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 优点           | 最简单；不需要额外进程管理；MCP SDK 提供 `StdioServerParameters` + `stdio_client`；直接在 Django request 生命周期内完成 |
| 缺点           | 需要在 API 容器中安装 `mcp` Python 包；每次 request 可能启动新进程（可用连接池缓解）                                    |
| 安全风险       | subprocess 使用 list args（shell=False）；timeout 控制；不把 prompt 拼入命令                                            |
| 适合 Phase 6.8 | ✅ 推荐                                                                                                                 |

### 方案 B：API 进程内调用 MCP SDK，plane-mcp-server 独立长驻进程

| 项目            | 说明                                               |
| --------------- | -------------------------------------------------- |
| 优点            | 进程复用，性能更好；不需要每次 request 启动新进程  |
| 缺点            | 需要进程管理（启动/重启/健康检查）；增加部署复杂度 |
| 安全风险        | 长驻进程需要安全管理；端口暴露风险                 |
| 是否需要 Docker | 不强制，但 Docker 更容易管理                       |
| 适合 Phase 6.8  | ⚠️ 可作为 Phase 6.9 优化                           |

### 方案 C：Docker sidecar / service

| 项目         | 说明                                                                   |
| ------------ | ---------------------------------------------------------------------- |
| 优点         | 完全隔离；独立扩展；最接近生产部署                                     |
| 缺点         | 需要修改 docker-compose；增加运维复杂度；当前阶段约束不允许修改 Docker |
| 安全风险     | 网络隔离需要正确配置                                                   |
| 为什么应后置 | Phase 10（Docker Packaging）再考虑                                     |

### 推荐结论

**Phase 6.8 推荐方案 A**：subprocess + stdio transport。

理由：

1. 最小改动，不需要修改 Docker
2. MCP SDK 提供标准 stdio client
3. `uvx` 可直接运行 plane-mcp-server
4. 安全：shell=False, timeout, tool allowlist 二次过滤
5. 保留 mock adapter 作为 fallback（`AI_MCP_ADAPTER=mock`）

---

## 7. 认证与权限风险

### 7.1 plane-mcp-server 认证方式

| 方式                  | 环境变量            | 说明                                               |
| --------------------- | ------------------- | -------------------------------------------------- |
| API Key（stdio 模式） | `PLANE_API_KEY`     | Workspace 级 API key，通过 `X-Api-Key` header 发送 |
| OAuth（HTTP 模式）    | OAuth provider 配置 | 用户级 token，需要 OAuth flow                      |

### 7.2 权限模型差异

| 项目     | 当前 mock adapter              | plane-mcp-server（stdio）          |
| -------- | ------------------------------ | ---------------------------------- |
| 认证方式 | request.user（Django session） | PLANE_API_KEY（workspace API key） |
| 权限范围 | 当前用户的 project membership  | workspace 级别，可访问所有 project |
| 用户隔离 | ✅ 有                          | ❌ 无（API key 绕过用户权限）      |
| 可审计性 | 可关联到具体用户               | 只能关联到 API key                 |

### 7.3 最大权限风险

**plane-mcp-server 使用 workspace API key，绕过用户权限。**

具体表现：

- 当前 mock adapter 检查 `ProjectMember`，只返回用户有权限的数据
- plane-mcp-server 使用 `PLANE_API_KEY`，可以访问 workspace 下所有 project
- 这意味着 MCP server 可以返回当前用户无权访问的数据

### 7.4 是否能代表当前用户调用 MCP

**stdio 模式下不能。** 原因：

- stdio 模式只支持 `PLANE_API_KEY`（workspace 级）
- 不支持 per-user token 传递
- OAuth 模式支持用户级 token，但需要 HTTP transport + OAuth flow，复杂度高

### 7.5 Phase 6.8 建议

**暂时使用 API key + 工具白名单二次过滤**：

1. plane-mcp-server 使用 `PLANE_API_KEY` 调用 Plane API
2. MCP client（我们的代码）对返回结果做二次过滤：
   - 只允许 read-only 工具
   - 禁止所有写操作
3. 后续阶段再实现 per-user token（需要 OAuth flow）

### 7.6 当前 mock adapter 与真实 MCP server 的权限模型差异

| 维度           | mock adapter                | plane-mcp-server                    |
| -------------- | --------------------------- | ----------------------------------- |
| 用户级权限     | ✅ 有（ProjectMember 检查） | ❌ 无（workspace API key）          |
| workspace 隔离 | ✅ 有                       | ✅ 有（API key 绑定 workspace）     |
| project 隔离   | ✅ 有（membership 检查）    | ❌ 无（API key 可访问所有 project） |
| 数据范围       | 只返回用户有权访问的        | 返回 workspace 下所有数据           |

---

## 8. 工具白名单映射

| 当前 mock 工具名     | plane-mcp-server 工具名 | 是否存在 | 是否只读 | 参数差异                                           |
| -------------------- | ----------------------- | -------- | -------- | -------------------------------------------------- |
| `get_me`             | `get_me`                | ✅       | ✅ 只读  | 无参数                                             |
| `list_projects`      | `list_projects`         | ✅       | ✅ 只读  | MCP 支持 cursor/per_page/expand/fields/order_by    |
| `retrieve_project`   | `retrieve_project`      | ✅       | ✅ 只读  | 参数相同                                           |
| `list_work_items`    | `list_work_items`       | ✅       | ✅ 只读  | MCP 支持更多过滤参数（assignee_ids, state_ids 等） |
| `search_work_items`  | `search_work_items`     | ✅       | ✅ 只读  | MCP 搜索整个 workspace                             |
| `retrieve_work_item` | `retrieve_work_item`    | ✅       | ✅ 只读  | 参数相同                                           |
| `list_states`        | `list_states`           | ✅       | ✅ 只读  | 参数相同                                           |
| `list_labels`        | `list_labels`           | ✅       | ✅ 只读  | 参数相同                                           |
| `list_cycles`        | `list_cycles`           | ✅       | ✅ 只读  | 参数相同                                           |
| `list_modules`       | `list_modules`          | ✅       | ✅ 只读  | 参数相同                                           |

**plane-mcp-server 额外的写操作工具（必须禁止）**：

| 工具名                                | 类型 |
| ------------------------------------- | ---- |
| `create_project`                      | 写   |
| `update_project`                      | 写   |
| `delete_project`                      | 写   |
| `create_work_item`                    | 写   |
| `update_work_item`                    | 写   |
| `delete_work_item`                    | 写   |
| `create_state`                        | 写   |
| `update_state`                        | 写   |
| `delete_state`                        | 写   |
| `create_label`                        | 写   |
| `update_label`                        | 写   |
| `delete_label`                        | 写   |
| `create_cycle`                        | 写   |
| `update_cycle`                        | 写   |
| `delete_cycle`                        | 写   |
| `create_module`                       | 写   |
| `update_module`                       | 写   |
| `delete_module`                       | 写   |
| `archive_cycle` / `unarchive_cycle`   | 写   |
| `archive_module` / `unarchive_module` | 写   |
| `add_work_items_to_cycle`             | 写   |
| `remove_work_item_from_cycle`         | 写   |
| `transfer_cycle_work_items`           | 写   |
| `add_work_items_to_module`            | 写   |
| `remove_work_item_from_module`        | 写   |

---

## 9. Phase 6.8 最小真实 MCP Client 设计

### 9.1 新增配置项

| 变量名                  | 默认值                       | 说明                                                            |
| ----------------------- | ---------------------------- | --------------------------------------------------------------- |
| `AI_MCP_ADAPTER`        | `mock`                       | 适配器类型：`mock`（当前 DB 直查）或 `stdio`（真实 MCP server） |
| `AI_MCP_SERVER_COMMAND` | `uvx plane-mcp-server stdio` | MCP server 启动命令                                             |
| `AI_MCP_SERVER_TIMEOUT` | `30`                         | MCP server 请求超时（秒）                                       |

### 9.2 架构设计

```
┌─────────────────────────────────────────────────┐
│  WorkspaceGPTIntegrationEndpoint.post()          │
│  mode == "mcp"                                   │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  execute_mcp_request()                           │
│  1. Check ENABLE_AI_MCP_RUNTIME                  │
│  2. Parse intent                                 │
│  3. Validate tool is read-only (allowlist)       │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  AI_MCP_ADAPTER dispatch                         │
│  ┌─────────────┐    ┌──────────────────────┐    │
│  │ mock adapter │    │ stdio adapter (new)  │    │
│  │ (Phase 6)   │    │ 1. Spawn subprocess  │    │
│  │ Direct DB   │    │ 2. MCP stdio client  │    │
│  │ query       │    │ 3. Call tool         │    │
│  │             │    │ 4. Parse result      │    │
│  └─────────────┘    └──────────────────────┘    │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  Write operation check (二次过滤)                │
│  - Reject if tool not in READ_ONLY_TOOLS         │
│  - Reject if tool matches PROHIBITED_PATTERNS    │
└─────────────────────────────────────────────────┘
```

### 9.3 安全要求

| 要求                      | 实现方式                                   |
| ------------------------- | ------------------------------------------ |
| subprocess 使用 list args | `["uvx", "plane-mcp-server", "stdio"]`     |
| shell=False               | 默认行为                                   |
| timeout                   | `asyncio.wait_for()` 或 subprocess timeout |
| 不把 prompt 拼入命令      | 命令固定，prompt 通过 stdin 传递           |
| 不输出 stderr 原文        | 只记录到 server log，不返回给用户          |
| tool allowlist 二次过滤   | 在 MCP client 层再次检查                   |
| 禁止写工具                | READ_ONLY_TOOLS 白名单                     |
| fail closed               | 异常时返回安全错误消息                     |

### 9.4 Fallback 策略

- `AI_MCP_ADAPTER=mock`：使用当前 mock/direct DB adapter（Phase 6 行为）
- `AI_MCP_ADAPTER=stdio`：使用真实 MCP server
- stdio 不可用时：返回安全错误，不自动退回 mock（避免误导用户认为数据来自 MCP）

---

## 10. 是否需要 Docker

**Phase 6.8 不需要。** 方案 A（subprocess + stdio）可以在不修改 Docker 的前提下做 dev-only 集成。

Docker sidecar 应后置到 Phase 10。

---

## 11. 是否需要 migration

**否。**

---

## 12. 是否实现写操作

**否。** Phase 6.8 只集成 read-only 工具。

---

## 13. 是否建议进入 Phase 6.8

**是。** 环境已具备（uv/uvx 可用，plane-mcp-server 可运行），可以开始实现 stdio adapter。

---

## 14. 是否建议进入写操作阶段

**否。** 建议先完成真实 MCP server read-only 集成，再考虑写操作。

---

## 15. 已知限制

| 限制                    | 说明                             | 后续方案                               |
| ----------------------- | -------------------------------- | -------------------------------------- |
| 不能代表当前用户        | stdio 模式使用 workspace API key | 后续可用 OAuth + HTTP transport        |
| API key 权限过宽        | 可访问 workspace 下所有 project  | 工具白名单二次过滤                     |
| MCP SDK 未在系统 python | 只在 uvx 环境内                  | 可通过 `uvx --from mcp` 或 pip install |
| 每次请求启动新进程      | 性能开销                         | 后续可用长驻进程或连接池               |

---

## 16. Phase 6.8 实施记录（2026-05-28）

Phase 6.8 已按本文档调研结论实施，详见 [`PHASE_6_8_REAL_MCP_STDIO_ADAPTER_REPORT.md`](./PHASE_6_8_REAL_MCP_STDIO_ADAPTER_REPORT.md)。

**实施结果**：

- ✅ 新增 `mcp_stdio_adapter.py`（JSON-RPC over subprocess）
- ✅ `mcp_runtime.py` 添加 adapter dispatch（mock/stdio）
- ✅ 默认 adapter 为 mock
- ✅ 不自动 fallback
- ✅ 安全措施全部实现（shell=False, timeout, 错误脱敏）
- ⚠️ 未实现后置权限过滤
