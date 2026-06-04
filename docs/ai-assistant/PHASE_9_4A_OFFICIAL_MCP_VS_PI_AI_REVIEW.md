# 第 9.4A 阶段报告：Official MCP vs Internal pi-ai Architecture Review

> 日期：2026-06-03
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：架构审查完成，建议切回官方 MCP 路线

---

## 1. 审查背景

用户测试自然语言 "在项目 AI Test Project 下新增一个 work item，命名为 asdfg" 失败，返回 "Could not determine which MCP tool to call"。这暴露了 pi-ai 路线的根本问题：手写 parser 无法覆盖自然语言变体。

---

## 2. 官方 MCP 项目定位

| 项目     | 值                                       |
| -------- | ---------------------------------------- |
| 包名     | `plane-mcp-server`                       |
| 安装     | `uvx plane-mcp-server`                   |
| 运行方式 | stdio / HTTP / SSE                       |
| 认证     | `PLANE_API_KEY` + `PLANE_WORKSPACE_SLUG` |
| 底层     | 调用 Plane REST API，不直接写 DB         |

---

## 3. 官方 MCP Tool Matrix

| 模块           | 工具                                                                   | 能力      |
| -------------- | ---------------------------------------------------------------------- | --------- |
| **Projects**   | list, create, retrieve, update, delete, members, features              | 完整 CRUD |
| **Work Items** | list, create, retrieve, retrieve_by_identifier, update, delete, search | 完整 CRUD |
| **Labels**     | list, create, retrieve, update, delete                                 | 完整 CRUD |
| **States**     | list, create, retrieve, update, delete                                 | 完整 CRUD |
| **Cycles**     | list, create, retrieve, update, delete, archive, add/remove items      | 完整 CRUD |
| **Modules**    | list, create, retrieve, update, delete, archive, add/remove items      | 完整 CRUD |
| **Users**      | get_me                                                                 | 只读      |
| **Workspaces** | members, features, update_features                                     | 部分      |

---

## 4. 能力矩阵对比

| 能力                    | 官方 MCP             | 当前 pi-ai   | 差距         |
| ----------------------- | -------------------- | ------------ | ------------ |
| list projects           | ✅                   | ✅ 手写      | 等价         |
| create work item        | ✅                   | ❌           | **缺失**     |
| update work item state  | ✅                   | ✅ 自研      | 等价         |
| update work item (通用) | ✅                   | ❌           | **缺失**     |
| delete work item        | ✅                   | ❌           | **缺失**     |
| search work items       | ✅                   | ✅ 手写      | 等价         |
| list/retrieve labels    | ✅                   | ✅ 手写      | 等价         |
| create label            | ✅                   | ❌           | **缺失**     |
| list/retrieve states    | ✅                   | ✅ 手写      | 等价         |
| list/retrieve cycles    | ✅                   | ✅ 手写      | 等价         |
| list/retrieve modules   | ✅                   | ✅ 手写      | 等价         |
| get_me                  | ✅                   | ✅           | 等价         |
| 自然语言理解            | LLM function calling | 手写 parser  | **巨大差距** |
| tool schema             | ✅ 自动              | ❌ 手动      | **差距**     |
| 权限校验                | Plane API 内置       | 自研 DB 查询 | 等价         |
| 审计日志                | ❌                   | ✅ 自研      | pi-ai 优势   |
| 确认流程                | ❌                   | ✅ 自研      | pi-ai 优势   |
| Web UI                  | ❌                   | ✅ 自研      | pi-ai 优势   |

---

## 5. 用户真实场景支持

| 场景                        | 官方 MCP                    | pi-ai            |
| --------------------------- | --------------------------- | ---------------- |
| "新增 work item asdfg"      | ✅ `create_work_item`       | ❌ parser 不支持 |
| "AITEST-1 改为 In Progress" | ✅ `update_work_item_state` | ✅ UUID 格式     |
| "列出所有 work items"       | ✅ `list_work_items`        | ✅               |
| "给 work item 添加 label"   | ✅ `update_work_item`       | ❌               |
| "分配给某成员"              | ✅ `update_work_item`       | ❌               |
| "查看项目状态"              | ✅ `list_states`            | ✅               |
| "总结本周完成项"            | ⚠️ 需 LLM 编排              | ❌               |

---

## 6. pi-ai 现状审查

| 模块               | 现状                     | 我们新增 | 可维护 | 应保留             |
| ------------------ | ------------------------ | -------- | ------ | ------------------ |
| intent parser      | 手写关键词匹配           | 部分     | 低     | ❌ 废弃            |
| tool router        | 手写 if/elif             | 部分     | 低     | ❌ 废弃            |
| mock adapter       | 直接 DB 查询             | ✅       | 中     | ⚠️ 仅 dev fallback |
| stdio adapter      | JSON-RPC over subprocess | ✅       | 中     | ⚠️ 仅测试          |
| proposed_action    | 自动生成                 | ✅       | 高     | ✅ 保留            |
| confirmation card  | Web UI                   | ✅       | 高     | ✅ 保留            |
| confirm execution  | ORM + activity dispatch  | ✅       | 高     | ✅ 保留            |
| audit logger       | Python logger + DB       | ✅       | 高     | ✅ 保留            |
| AIAuditEvent model | Django model + migration | ✅       | 高     | ✅ 保留            |
| audit read API     | admin-only endpoint      | ✅       | 高     | ✅ 保留            |
| retention command  | management command       | ✅       | 高     | ✅ 保留            |

**结论**：pi-ai 的价值在于 **UI、confirmation、audit**，不在于手写 parser 和 tool router。

---

## 7. 推荐架构决策

**推荐方案 C：混合路线 — 官方 MCP 负责工具执行，项目内保留 confirmation / audit / UI**

### 架构

```
User → pi-chat UI → AI Gateway (项目内)
    → LLM 选择 MCP tool + 参数
    → proposed_action + confirmation card
    → 用户 Confirm
    → 调用官方 MCP server write tool
    → audit proposed → confirmed → executed
```

### 为什么不选纯 pi-ai (方案 A)

1. 手写 parser 无法覆盖自然语言变体
2. 缺少 create_work_item, update_work_item 等核心工具
3. 扩展成本高，每新增一个工具需要手写 parser + DB adapter
4. 与 Plane API 重复造轮子

### 为什么不选纯官方 MCP (方案 B)

1. 官方 MCP 没有 confirmation flow
2. 官方 MCP 没有审计日志
3. 官方 MCP 没有 Web UI
4. 直接调用 MCP write 工具跳过了安全确认

### 混合路线优势

1. 官方 MCP 负责 Plane API 调用（已有完整 CRUD）
2. 项目内负责安全层（confirmation + audit + UI）
3. 不重复造轮子
4. 可扩展性好（官方 MCP 更新工具，项目内自动受益）

---

## 8. 当前 9.3.8 成果保留清单

| 成果                           | 保留 | 迁移方式                    |
| ------------------------------ | ---- | --------------------------- |
| AIAuditEvent model + migration | ✅   | 不变                        |
| audit_logger.py                | ✅   | 不变                        |
| confirmation card UI           | ✅   | 不变                        |
| proposed_action 逻辑           | ✅   | 改为从 MCP tool schema 生成 |
| confirm execution path         | ✅   | 改为调用 MCP write tool     |
| AIAuditEvent API               | ✅   | 不变                        |
| retention command              | ✅   | 不变                        |
| intent parser                  | ❌   | 废弃，改用 LLM              |
| tool router                    | ❌   | 废弃，改用 MCP tool list    |
| mock adapter                   | ⚠️   | 仅 dev fallback             |
| stdio adapter                  | ⚠️   | 改为调用官方 MCP server     |

---

## 9. 最小切回方案

### 新分支

`feat/ai-official-mcp-confirmed-actions`

### 基于

`feat/ai-phase-6-mcp-readonly-runtime`（保留已验证成果）

### 切回目标

1. 官方 MCP server 负责 Plane tools
2. 项目内 AI gateway 负责：
   - 选择 tool（通过 LLM function calling 或 MCP tool schema）
   - 展示 preview
   - proposed_action
   - confirmation card
   - Confirm 后调用 MCP write tool
   - audit proposed → confirmed → executed
   - token 安全
   - raw_result_returned=false
3. 不再用手写 parser 作为主路径
4. 不再用 direct DB adapter 作为主路径
5. direct DB/mock adapter 只作为 dev fallback

---

## 10. Spike 结论

官方 MCP server 可通过 `uvx plane-mcp-server stdio` 运行，支持完整 CRUD。无需额外 spike。

---

## 11. 建议 PR 策略

**不建议在当前分支直接 PR。** 原因：

1. 包含 71 commits 和 78 个内部文档
2. 手写 parser 代码不应进入 upstream

**建议**：

1. 先在当前分支完成切回官方 MCP
2. 然后创建 clean PR branch
3. 只包含必要代码和精简文档
