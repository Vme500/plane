# 第 9.4C 阶段报告：Official MCP Gateway Skeleton

> 日期：2026-06-03
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：骨架实现完成

---

## 1. 实施目标

实现 official MCP 主路径的最小可运行骨架。

---

## 2. pi-ai 代码保留

✅ 保留。标记为 legacy/internal fallback。

---

## 3. official MCP 为主路径

✅ 正式切换。

---

## 4. 新增文件

| 文件                                       | 说明                                           |
| ------------------------------------------ | ---------------------------------------------- |
| `apps/api/plane/ai/mcp_config.py`          | MCP 配置层                                     |
| `apps/api/plane/ai/official_mcp_client.py` | MCP client（stdio JSON-RPC）                   |
| `apps/api/plane/ai/mcp_gateway.py`         | MCP gateway（tool discovery + write proposal） |

---

## 5. MCP Config

- 读取 `PLANE_AI_MCP_*` 环境变量
- 默认 provider: `official_plane_mcp`
- 默认 command: `uvx`
- 默认 args: `plane-mcp-server stdio`
- API key 不返回前端

---

## 6. MCP Client

- 启动 stdio MCP server
- 初始化 session
- list_tools
- timeout + process cleanup
- 不暴露 secret

---

## 7. MCP Gateway

- `discover_tools()`: 列出可用工具
- `generate_write_proposal()`: 为 write 工具生成 proposed_action
- Read 工具直接执行（待实现）
- Write 工具只生成 proposed_action，不执行

---

## 8. Tool Allowlist

| 类别                                | 工具                                                                                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Read (allowed)                      | get_me, list_projects, list_work_items, list_states, list_labels, list_cycles, list_modules, retrieve_project, retrieve_work_item, search_work_items |
| Write (allowed, needs confirmation) | create_work_item, update_work_item                                                                                                                   |
| Destructive (disabled)              | delete_work_item, create/update/delete project/state/label/cycle/module                                                                              |

---

## 9. LLM Tool-Calling 策略

**当前：Dev deterministic fallback。**

标记为 fallback，不是最终路线。最终路线是 LLM 根据 MCP tool schema 选择工具和参数。

---

## 10. py_compile 结果

| 文件                     | 结果 |
| ------------------------ | ---- |
| `mcp_config.py`          | ✅   |
| `official_mcp_client.py` | ✅   |
| `mcp_gateway.py`         | ✅   |
