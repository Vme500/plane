# 第 6 阶段报告：MCP Runtime Read-Only

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                              |
| ---------- | ----------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`          |
| 基于       | `feat/ai-phase-5-ai-settings-page` (16f2f1b7bb) |
| 工作区状态 | 干净（无未提交修改）                            |

---

## 2. 修改文件清单

### 新增文件

| 文件                               | 说明                           |
| ---------------------------------- | ------------------------------ |
| `apps/api/plane/ai/__init__.py`    | AI 模块初始化                  |
| `apps/api/plane/ai/mcp_tools.py`   | MCP read-only 工具白名单和实现 |
| `apps/api/plane/ai/mcp_runtime.py` | MCP runtime 核心逻辑           |

### 修改文件

| 文件                                                             | 变更                                                 |
| ---------------------------------------------------------------- | ---------------------------------------------------- |
| `apps/api/plane/app/views/external/base.py`                      | 扩展 `WorkspaceGPTIntegrationEndpoint` 支持 MCP mode |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | 添加 MCP mode 切换和响应处理                         |

### 文档文件

| 文件                                                       | 变更                  |
| ---------------------------------------------------------- | --------------------- |
| `docs/ai-assistant/PHASE_6_MCP_READONLY_RUNTIME_REPORT.md` | 新增阶段报告          |
| `docs/ai-assistant/AI_ROADMAP.md`                          | 更新 Phase 6 状态     |
| `docs/ai-assistant/PHASE_2_ARCHITECTURE_DECISION.md`       | 添加 Phase 6 实施记录 |

---

## 3. MCP runtime 放在哪里

| 项目     | 值                                                     |
| -------- | ------------------------------------------------------ |
| 模块位置 | `apps/api/plane/ai/`                                   |
| 核心文件 | `mcp_runtime.py` — runtime 逻辑、intent 解析、请求执行 |
| 工具文件 | `mcp_tools.py` — read-only 白名单、mock 实现           |
| 初始化   | `__init__.py`                                          |

---

## 4. 是否真实调用 plane-mcp-server

**否。** 原因：

1. 当前环境没有安装 MCP SDK (`mcp` Python 包)
2. 没有找到 `plane-mcp-server` 包或可执行文件
3. 没有配置 MCP server 连接信息

**当前实现**：使用 mock 实现，直接查询 Plane 数据库返回结果。

**后续集成**：

- 安装 MCP SDK：`pip install mcp`
- 配置 plane-mcp-server 连接
- 将 `execute_tool_mock()` 替换为真实的 MCP client 调用

---

## 5. read-only 工具白名单

| 工具名               | 说明               |
| -------------------- | ------------------ |
| `get_me`             | 获取当前用户信息   |
| `list_projects`      | 列出工作区所有项目 |
| `retrieve_project`   | 获取项目详情       |
| `list_work_items`    | 列出项目工作项     |
| `search_work_items`  | 搜索工作项         |
| `retrieve_work_item` | 获取工作项详情     |
| `list_states`        | 列出项目状态       |
| `list_labels`        | 列出项目标签       |
| `list_cycles`        | 列出项目周期       |
| `list_modules`       | 列出项目模块       |

---

## 6. 禁止的写操作类别

| 模式       | 说明     |
| ---------- | -------- |
| `create*`  | 创建操作 |
| `update*`  | 更新操作 |
| `delete*`  | 删除操作 |
| `assign*`  | 分配操作 |
| `move*`    | 移动操作 |
| `archive*` | 归档操作 |
| `bulk*`    | 批量操作 |
| `import*`  | 导入操作 |
| `upload*`  | 上传操作 |
| `set_*`    | 设置操作 |
| `add_*`    | 添加操作 |
| `remove_*` | 移除操作 |

---

## 7. endpoint 如何区分 standard / mcp mode

**请求格式**：

```json
{
  "prompt": "...",
  "task": "chat",
  "mode": "mcp" // 或 "standard"（默认）
}
```

**后端逻辑**（`apps/api/plane/app/views/external/base.py`）：

1. 检查 `mode` 参数，默认为 `"standard"`
2. 如果 `mode == "mcp"`：
   - 检查 `ENABLE_AI_MCP_RUNTIME` 是否开启
   - 解析用户 prompt 确定工具意图
   - 执行 read-only 工具
   - 返回结构化响应
3. 如果 `mode == "standard"`：
   - 保持原有 prompt-response 行为

---

## 8. 前端如何切换 MCP mode

**UI 组件**：

- 当 `config.enable_ai_mcp_runtime == true` 时，显示 mode 切换按钮
- 两个按钮：`Standard Chat` 和 `MCP Read-only`
- 默认为 `Standard Chat`
- 选择 `MCP Read-only` 时显示提示："Read-only queries only"

**请求处理**：

- 选择 MCP mode 时，payload 增加 `mode: "mcp"`
- 输入框 placeholder 根据 mode 变化

---

## 9. tool result 如何展示

**展示方式**：

1. MCP 工具摘要：`[MCP] tool_name: Found X item(s)`
2. 详细结果：格式化的文本内容
3. 错误信息：`[MCP] tool_name: Error message`

**不展示的内容**：

- 不展示 JSON.stringify 完整对象
- 不展示 headers/config/request/stack
- 不展示 token/API key

---

## 10. 是否新增 migration

**否。**

---

## 11. 是否修改 Docker

**否。**

---

## 12. 是否实现写操作

**否。** 只实现 read-only 工具。

---

## 13. 是否实现 Claude Code Runtime

**否。**

---

## 14. typecheck/lint 结果

| 检查              | 结果                               |
| ----------------- | ---------------------------------- |
| Python py_compile | **通过**（4 个文件）               |
| typecheck         | **通过**（exit 0）                 |
| lint              | **通过**（0 errors，997 warnings） |

---

## 15. 已知问题

1. **Mock 实现**：当前使用数据库直接查询作为 mock，不是真实的 MCP server 调用
2. **Intent 解析**：使用简单的关键词匹配，不是 LLM function calling
3. **错误处理**：基本错误处理，可能需要更详细的错误分类
4. **性能**：直接数据库查询可能在大数据量时有性能问题

---

## 16. Phase 7 建议

### Phase 7: Write Operation Confirmation

- 添加写操作工具（create, update work items）
- 执行前显示确认对话框
- 参数审查 UI
- 执行反馈
- 所有写操作记录到审计日志

### 集成真实 MCP Server

- 安装 MCP SDK
- 配置 plane-mcp-server 连接
- 替换 mock 实现为真实 MCP client 调用
- 添加连接状态检查

### Intent 解析优化

- 使用 LLM function calling 替代关键词匹配
- 支持更复杂的自然语言查询
- 添加上下文感知（当前项目、当前工作项等）

---

## 17. Phase 6.6 修复记录（2026-05-28）

Phase 6.5 安全审查发现的权限问题已在 Phase 6.6 中修复，详见 [`PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md`](./PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md)。

**主要变更**：

- `execute_tool_mock()` 签名变更：`user_id: str` → `user`（Django User 对象）
- `execute_mcp_request()` 签名变更：`user_id: str` → `user`
- 所有工具添加 workspace / project membership 校验
- Issue 工具改用 `Issue.issue_objects`
- 所有 list 工具添加返回数量限制

---

## 18. Phase 6.7 调研记录（2026-05-28）

Phase 6.7 完成了真实 plane-mcp-server 集成调研，详见 [`PHASE_6_7_REAL_MCP_INTEGRATION_RESEARCH.md`](./PHASE_6_7_REAL_MCP_INTEGRATION_RESEARCH.md)。

**关键发现**：

- `plane-mcp-server` 可通过 `uvx plane-mcp-server stdio` 运行
- 所有 10 个 read-only 工具在 plane-mcp-server 中有对应工具名
- 认证使用 `PLANE_API_KEY`（workspace 级 API key），不能代表当前用户
- 推荐 subprocess + stdio transport 方案（不修改 Docker）
