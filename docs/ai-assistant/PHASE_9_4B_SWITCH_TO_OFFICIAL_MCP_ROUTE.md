# 第 9.4B 阶段报告：Switch to Official MCP Server Route

> 日期：2026-06-03
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：架构切换设计完成

---

## 1. 为什么停止 pi-ai 主路径

1. 手写 parser 无法覆盖自然语言变体
2. 缺少 create_work_item, update_work_item 等核心工具
3. 扩展成本高，每新增工具需手写 parser + DB adapter
4. 与 Plane API 重复造轮子
5. 官方 MCP 已有 109 个工具，pi-ai 只有 10 个

---

## 2. 为什么切回官方 MCP

1. `plane-mcp-server` 可通过 `uvx` 安装
2. 支持完整 CRUD：create/update/delete work_item, project, label, state, cycle, module
3. 使用 Plane REST API，不直接写 DB
4. 有 tool schema，可被 LLM function calling 使用
5. 活跃维护，持续更新

---

## 3. 官方 MCP Spike 结果

| 检查项            | 结果                            |
| ----------------- | ------------------------------- |
| 是否能启动        | ✅ `uvx plane-mcp-server stdio` |
| 是否能 list tools | ✅ 109 个工具                   |
| create_work_item  | ✅ 存在                         |
| update_work_item  | ✅ 存在                         |
| delete_work_item  | ✅ 存在                         |
| list_projects     | ✅ 存在                         |
| list_work_items   | ✅ 存在                         |
| list_states       | ✅ 存在                         |

---

## 4. 新架构

```
User
  → Plane AI UI (pi-chat / AI panel)
  → Plane AI Gateway API (项目内)
  → LLM tool-calling / MCP client (项目内)
  → official plane-mcp-server (uvx)
  → Plane API
  → audit / confirmation / response sanitization (项目内)
```

---

## 5. 职责划分

### 官方 plane-mcp-server

- 提供 Plane read/write tools
- 通过 Plane API 执行 CRUD
- 不由项目内 direct DB adapter 重复实现

### 项目内保留

- MCP server 配置 UI
- MCP connection test
- MCP tool discovery
- tool allowlist
- LLM tool selection
- proposed_action
- confirmation card
- Confirm 后执行
- audit proposed → confirmed → executed
- token 安全
- raw_result_returned=false
- permission/safety gateway

### pi-ai 遗留代码

- 保留，不删除
- 标记为 legacy/internal route
- 不再作为主 tool execution 路径
- 不再继续补手写 parser

---

## 6. Tool Allowlist 设计

### Read tools（默认允许）

- get_me
- list_projects
- list_work_items
- list_states
- list_labels
- list_cycles
- list_modules
- retrieve_project
- retrieve_work_item
- search_work_items

### Write tools（初期允许，需 confirmation）

- create_work_item
- update_work_item

### 暂不开放

- delete_work_item
- create_project / update_project / delete_project
- delete / archive tools
- permission / settings changes

---

## 7. Confirmation Policy

所有 write tools 必须走：

```
proposed_action → Confirm → execute
```

不能由 LLM 直接执行 write。

---

## 8. Audit Policy

复用当前 9.3.8 成果：

- AIAuditEvent model
- audit_logger.py
- retention command
- proposed → confirmed → executed
- raw_result_returned=false
- token 不显示、不输出、不入库

---

## 9. 9.3.8 成果复用清单

| 成果                           | 复用                           |
| ------------------------------ | ------------------------------ |
| AIAuditEvent model + migration | ✅                             |
| audit_logger.py                | ✅                             |
| confirmation card UI           | ✅                             |
| proposed_action 逻辑           | ✅ 改为从 MCP tool schema 生成 |
| confirm execution path         | ✅ 改为调用 MCP write tool     |
| AIAuditEvent API               | ✅                             |
| retention command              | ✅                             |
| intent parser                  | ❌ 废弃                        |
| tool router                    | ❌ 废弃                        |
| mock adapter                   | ⚠️ 仅 dev fallback             |
