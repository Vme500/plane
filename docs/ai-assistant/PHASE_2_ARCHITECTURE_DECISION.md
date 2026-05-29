# 第 2 阶段：基于现有 AI 基础设施的架构决策

> 日期：2026-05-28
> 分支：feat/ai-phase-1-research
> 状态：规划文档，不涉及功能代码修改

---

## 1. 第 1 阶段误判说明

### 1.1 误判内容

第 1 阶段调研报告（`PHASE_1_CODE_RESEARCH.md`）中写道：

> "后端 AI 端点似乎已移除：前端调用的 `/api/workspaces/{slug}/ai-assistant/` 和 `/api/workspaces/{slug}/rephrase-grammar/` 在当前 `apps/api/plane/app/urls/workspace.py` 中不存在。"

### 1.2 纠正

第 1.5 阶段专项核验（`PHASE_1_5_EXISTING_AI_INFRA_RESEARCH.md`）确认：

- `/api/workspaces/{slug}/ai-assistant/` **实际存在**，定义在 `apps/api/plane/app/urls/external.py`
- `/api/workspaces/{slug}/projects/{project_id}/ai-assistant/` **实际存在**
- 对应的 view 类 `WorkspaceGPTIntegrationEndpoint` 和 `GPTIntegrationEndpoint` 在 `apps/api/plane/app/views/external/base.py` 中实现
- 使用 OpenAI SDK，支持 OpenAI / Anthropic / Gemini 三个 provider

**原因**：第 1 阶段只检查了 `workspace.py`，没有检查 `external.py`。

### 1.3 唯一确实缺失的 endpoint

`/api/workspaces/{slug}/rephrase-grammar/` — 该 endpoint 在后端不存在，但它是页面编辑器 AI 功能，不是本项目重点。

---

## 2. 现有基础设施复用决策

### 2.1 复用 pi-chat 侧边栏入口

| 项目       | 决策                                                                   |
| ---------- | ---------------------------------------------------------------------- |
| 侧边栏入口 | 复用 `SIDEBAR_USER_MENU_ITEMS` 中已有的 `pi-chat` 项                   |
| 图标       | 复用 `PiChatLogo`（`packages/propel/src/icons/sub-brand/pi-chat.tsx`） |
| i18n key   | 复用 `sidebar.pi_chat` 和 `common.pi_chat`，必要时修改显示文案         |
| href       | 复用 `/${workspaceSlug}/pi-chat/`                                      |
| 路径检测   | 复用 `useWorkspacePaths` 中的 `isAiPath`                               |

**不新增 `ai-assistant` 侧边栏入口**，避免重复。

### 2.2 复用 AIService

| 项目             | 决策                                                                  |
| ---------------- | --------------------------------------------------------------------- |
| 共享包 AIService | 复用 `packages/services/src/ai/ai.service.ts`，添加新方法             |
| Web AIService    | 复用 `apps/web/core/services/ai.service.ts`，添加新方法               |
| 现有方法         | 保留 `prompt()` / `createGptTask()` 向后兼容                          |
| 新增方法         | 添加 `chat()`, `confirmAction()`, `getSettings()`, `updateSettings()` |

**不新建 `MCPAIService`**，避免代码重复。

### 2.3 复用后端 endpoint

| 项目          | 决策                                                          |
| ------------- | ------------------------------------------------------------- |
| 现有 endpoint | 复用 `WorkspaceGPTIntegrationEndpoint`，扩展支持 MCP 工具调用 |
| URL 路径      | 复用 `/api/workspaces/{slug}/ai-assistant/`                   |
| 权限          | 复用现有的 `@allow_permission` 装饰器                         |
| 新增 endpoint | 后续可新增 `/api/workspaces/{slug}/ai/settings/` 等           |

**不新建完全独立的 AI endpoint**，先扩展再迁移。

### 2.4 参考 has_llm_configured

| 项目                  | 决策                                     |
| --------------------- | ---------------------------------------- |
| has_llm_configured    | 保留，语义不变："LLM API key 是否已配置" |
| enable_ai_assistant   | 新增，语义："AI Assistant 功能是否启用"  |
| enable_ai_mcp_runtime | 新增，语义："MCP Runtime 是否启用"       |

---

## 3. 不采用的方案

| 方案                                 | 原因                               |
| ------------------------------------ | ---------------------------------- |
| 新增重复的 `ai-assistant` 侧边栏入口 | `pi-chat` 已存在，新增会造成重复   |
| 新建完全独立的 `MCPAIService`        | 现有 `AIService` 可扩展            |
| 恢复 `/rephrase-grammar/`            | 它是页面编辑器功能，不是本项目重点 |
| 第 2 阶段改 Docker                   | 过早，先跑通功能再考虑部署         |
| 第 2 阶段接 Claude Code Runtime      | 后置，先做简单 prompt-response     |

---

## 4. 推荐目标架构

```
┌─────────────────────────────────────────────────────────┐
│  Plane UI — pi-chat page                                │
│  (现有 pi-chat 入口 + 新建聊天页面)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  AIService (扩展)                                        │
│  - prompt() / createGptTask() — 现有，可用               │
│  - chat() — 新增，支持多轮对话                           │
│  - getSettings() / updateSettings() — 新增               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  WorkspaceGPTIntegrationEndpoint (扩展)                  │
│  - 现有 POST 方法 — 简单 prompt-response                 │
│  - 扩展支持 mode 参数（simple / mcp）                    │
│  - 扩展支持 MCP 工具调用                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  AI Runtime / MCP Client (新建)                          │
│  - 第一版：简单 prompt-response，不接 MCP                │
│  - 后续版：MCP client 调用 plane-mcp-server              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  plane-mcp-server (外部)                                 │
│  - stdio 或 HTTP/SSE transport                           │
│  - 提供只读 MCP 工具                                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Plane API (现有)                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Feature Flag 决策

### 5.1 Flag 定义

| Flag                    | 类型            | 默认值               | 语义                      |
| ----------------------- | --------------- | -------------------- | ------------------------- |
| `has_llm_configured`    | boolean（现有） | 取决于 `LLM_API_KEY` | LLM API key 是否已配置    |
| `enable_ai_assistant`   | boolean（新增） | `false`              | AI Assistant 功能是否启用 |
| `enable_ai_mcp_runtime` | boolean（新增） | `false`              | MCP Runtime 是否启用      |

### 5.2 组合逻辑

| enable_ai_assistant | has_llm_configured | pi-chat 页面状态               |
| ------------------- | ------------------ | ------------------------------ |
| false               | false              | 显示"AI Assistant 未启用"      |
| false               | true               | 显示"AI Assistant 未启用"      |
| true                | false              | 显示"LLM 未配置，请联系管理员" |
| true                | true               | 显示聊天界面，允许使用         |

### 5.3 环境变量

```env
# 现有
LLM_API_KEY=              # LLM API key（加密存储）
LLM_PROVIDER=openai       # LLM provider（openai / anthropic / gemini）
LLM_MODEL=gpt-4o-mini     # LLM model

# 新增
ENABLE_AI_ASSISTANT=false          # 是否启用 AI Assistant
ENABLE_AI_MCP_RUNTIME=false        # 是否启用 MCP Runtime
```

---

## 6. 第一版最小可开发目标

### 6.1 目标

让 `/:workspaceSlug/pi-chat/` 不再 404，显示最小可用的聊天页面。

### 6.2 功能范围

| 功能                               | 状态 |
| ---------------------------------- | ---- |
| pi-chat 路由                       | 新增 |
| pi-chat 页面组件                   | 新增 |
| 聊天输入框                         | 新增 |
| 消息显示                           | 新增 |
| 调用现有 `/ai-assistant/` endpoint | 复用 |
| 简单 prompt-response               | 可用 |
| enable_ai_assistant 检查           | 新增 |
| has_llm_configured 检查            | 复用 |
| "未启用" / "未配置" 提示           | 新增 |

### 6.3 不包含

| 功能                | 原因     |
| ------------------- | -------- |
| MCP 工具调用        | 后续阶段 |
| 写操作              | 后续阶段 |
| 确认机制            | 后续阶段 |
| 审计数据库模型      | 后续阶段 |
| Docker 修改         | 后续阶段 |
| Claude Code Runtime | 后续阶段 |

### 6.4 验收标准

- [ ] `/:workspaceSlug/pi-chat/` 路由存在
- [ ] 页面显示聊天界面
- [ ] `enable_ai_assistant=false` 时显示未启用提示
- [ ] `has_llm_configured=false` 时显示未配置提示
- [ ] 两者都满足时，可以输入问题并获得 AI 回答
- [ ] 不修改现有功能代码
- [ ] 不引入新的安全风险

---

## 7. 后续 MCP 接入目标

### 7.1 阶段划分

| 阶段  | 内容                                                                      |
| ----- | ------------------------------------------------------------------------- |
| MCP-1 | 在现有 endpoint 上增加 `mode` 参数或新增 endpoint                         |
| MCP-2 | 支持只读 MCP 工具（list_projects, list_work_items, search_work_items 等） |
| MCP-3 | 工具调用结果在 UI 中结构化展示                                            |
| MCP-4 | 写操作进入确认机制                                                        |

### 7.2 技术方案

1. 扩展 `WorkspaceGPTIntegrationEndpoint`，添加 `mode` 参数：
   - `mode=simple`：现有行为，直接 prompt-response
   - `mode=mcp`：通过 MCP client 调用 plane-mcp-server

2. 在后端新增 MCP client 模块：

   ```
   apps/api/plane/ai/
     __init__.py
     mcp_client.py    # MCP 协议客户端
     runtime.py       # AI 对话编排
     tools.py         # 工具定义和安全检查
   ```

3. 前端展示工具调用结果：
   - 聊天消息中显示"AI 正在查询项目列表..."
   - 结果以结构化卡片展示（项目卡片、工作项卡片等）

---

## 8. 风险

| 风险                                                     | 影响 | 缓解                             |
| -------------------------------------------------------- | ---- | -------------------------------- |
| 修改 pi-chat 可能影响官方未完成规划                      | 中   | 保持改动最小化，只添加路由和页面 |
| endpoint 当前命名和职责较旧                              | 低   | 后续可迁移到独立 `ai.py`         |
| has_llm_configured 和 enable_ai_assistant 关系需清晰     | 低   | 文档明确语义差异                 |
| 现有 LLMProvider 只做 prompt completion，不支持 tool use | 高   | 第一版不接 MCP，后续需要扩展     |
| MCP runtime 需要额外安全边界                             | 高   | 后续阶段单独处理                 |
| 上游更新可能覆盖我们的修改                               | 中   | 保持 fork 同步，改动模块化       |

---

## 9. 第 3 阶段实施记录（2026-05-28）

第 3 阶段已按本文档决策实施，详见 [`PHASE_3_PI_CHAT_PAGE_REPORT.md`](./PHASE_3_PI_CHAT_PAGE_REPORT.md)。

**实际实施范围**：

- ✅ 复用 pi-chat 侧边栏入口（未修改）
- ✅ 新增 `/:workspaceSlug/pi-chat` 路由
- ✅ 新增页面组件（page.tsx + layout.tsx + header.tsx）
- ✅ 使用 `has_llm_configured` 检查 LLM 配置状态
- ✅ 调用现有 `AIService.createGptTask()` 做 prompt-response
- ⏳ `enable_ai_assistant` flag 控制推迟到 Phase 4

---

## 10. 第 4 阶段实施记录（2026-05-28）

第 4 阶段已按本文档决策实施，详见 [`PHASE_4_FEATURE_FLAG_PROMPT_REPORT.md`](./PHASE_4_FEATURE_FLAG_PROMPT_REPORT.md)。

**实际实施范围**：

- ✅ 新增 `enable_ai_assistant` 和 `enable_ai_mcp_runtime` feature flags
- ✅ 后端从环境变量读取，识别 "1"/"true" 为 true
- ✅ pi-chat 页面三级 gating：disabled → not configured → chat
- ✅ 响应展示优化（移除 JSON.stringify 兜底）
- ✅ 内存级 conversation history
- ✅ 修复 no-array-index-key lint warning
- ⏳ sidebar 入口 gating 跳过（当前 sidebar 中 pi-chat 是死代码）

---

## 11. 第 5 阶段实施记录（2026-05-28）

第 5 阶段已按本文档决策实施，详见 [`PHASE_5_AI_SETTINGS_PAGE_REPORT.md`](./PHASE_5_AI_SETTINGS_PAGE_REPORT.md)。

**实际实施范围**：

- ✅ 新增 "AI Assistant" 到 Workspace Settings sidebar（FEATURES 分类）
- ✅ 新增只读设置页面，展示 AI Assistant 状态
- ✅ 展示 enable_ai_assistant、enable_ai_mcp_runtime、has_llm_configured 三个状态
- ✅ 不展示 API key，不展示完整环境变量值
- ✅ 无表单、无保存按钮
- ✅ 不新增后端 API
- ✅ 不新增 migration
- ✅ 不修改 Docker
- ✅ typecheck 通过
- ✅ lint 通过（0 errors）

---

## 12. 第 6 阶段实施记录（2026-05-28）

第 6 阶段已按本文档决策实施，详见 [`PHASE_6_MCP_READONLY_RUNTIME_REPORT.md`](./PHASE_6_MCP_READONLY_RUNTIME_REPORT.md)。

**实际实施范围**：

- ✅ 新增 MCP runtime 模块（`apps/api/plane/ai/`）
- ✅ 定义 read-only 工具白名单（10 个工具）
- ✅ 实现 mock 工具执行（直接数据库查询）
- ✅ 扩展 `WorkspaceGPTIntegrationEndpoint` 支持 `mode=mcp`
- ✅ 前端添加 MCP mode 切换按钮
- ✅ 前端处理 MCP 响应展示
- ✅ 禁止所有写操作
- ✅ Python py_compile 通过
- ✅ typecheck 通过
- ✅ lint 通过（0 errors）
- ⏳ 未真实调用 plane-mcp-server（当前环境无 MCP SDK）

---

## 13. 第 6.6 阶段实施记录（2026-05-28）

第 6.6 阶段修复了 Phase 6.5 安全审查发现的权限问题，详见 [`PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md`](./PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md)。

**实际实施范围**：

- ✅ 修复跨 workspace 数据访问风险
- ✅ 修复 project 权限绕过风险
- ✅ 添加 soft-deleted 过滤（via SoftDeletionManager）
- ✅ 添加 archived 过滤（按 Plane 现有 API 模式）
- ✅ 添加返回数量限制
- ✅ 使用 `Issue.issue_objects` 替代 `Issue.objects`
- ✅ 错误消息脱敏（fail-closed）
- ✅ 传递 `request.user` 对象替代 user_id 字符串
- ✅ Python py_compile 通过
- ✅ typecheck 通过
- ✅ lint 通过（0 errors）

---

## 14. 第 6.7 阶段调研记录（2026-05-28）

第 6.7 阶段完成了真实 plane-mcp-server 集成调研，详见 [`PHASE_6_7_REAL_MCP_INTEGRATION_RESEARCH.md`](./PHASE_6_7_REAL_MCP_INTEGRATION_RESEARCH.md)。

**调研结论**：

- ✅ `plane-mcp-server` 可通过 `uvx plane-mcp-server stdio` 运行
- ✅ 所有 10 个 read-only 工具在 plane-mcp-server 中有对应工具
- ✅ 推荐方案 A：subprocess + stdio transport（不修改 Docker）
- ⚠️ 认证使用 workspace API key（`PLANE_API_KEY`），不能代表当前用户
- ⚠️ 需要在 client 层做写操作二次过滤
- ⏳ Phase 6.8 计划实现 stdio adapter

---

## 15. 第 6.8 阶段实施记录（2026-05-28）

第 6.8 阶段实现了真实 MCP stdio adapter prototype，详见 [`PHASE_6_8_REAL_MCP_STDIO_ADAPTER_REPORT.md`](./PHASE_6_8_REAL_MCP_STDIO_ADAPTER_REPORT.md)。

**实际实施范围**：

- ✅ 新增 `mcp_stdio_adapter.py`（JSON-RPC over subprocess）
- ✅ `mcp_runtime.py` 添加 adapter dispatch（mock/stdio）
- ✅ 默认 adapter 为 mock（stdio 需显式启用）
- ✅ 不自动 fallback
- ✅ tool allowlist 双重检查
- ✅ 写操作硬拒绝
- ✅ subprocess 安全措施（shell=False, timeout, 进程清理）
- ✅ 错误脱敏
- ✅ py_compile/typecheck/lint 通过
- ⚠️ 未实现后置权限过滤（stdio 使用 workspace API key，不能代表用户）

---

## 16. 第 6.9 阶段实施记录（2026-05-28）

第 6.9 阶段实现了 stdio adapter 安全闸门，详见 [`PHASE_6_9_MCP_STDIO_SAFETY_VALIDATION_REPORT.md`](./PHASE_6_9_MCP_STDIO_SAFETY_VALIDATION_REPORT.md)。

**实际实施范围**：

- ✅ 实现 `_filter_stdio_result()` 后置权限过滤
- ✅ `get_me` pass-through（无 workspace/project 数据）
- ✅ `list_projects` 与 accessible projects 交叉过滤
- ✅ `retrieve_project` 预验证 project access
- ✅ 其他 7 个 stdio 工具阻断
- ✅ fail-closed：所有异常路径返回安全错误
- ✅ MEMBER 无法获取非 member project 数据
- ✅ py_compile/typecheck/lint 通过

---

## 17. 第 6.9.1 阶段实施记录（2026-05-28）

第 6.9.1 阶段净化了 stdio adapter 允许工具的返回数据，详见 [`PHASE_6_9_1_MCP_STDIO_RESULT_SANITIZATION_REPORT.md`](./PHASE_6_9_1_MCP_STDIO_RESULT_SANITIZATION_REPORT.md)。

**实际实施范围**：

- ✅ `get_me` 不再返回 MCP raw result，改为 `_serialize_user_safe(request.user)`
- ✅ `list_projects` 不再从 MCP result 提取字段，改为本地 DB 查询
- ✅ `retrieve_project` 已使用本地 DB（无需修改）
- ✅ MCP raw result 永远不返回前端
- ✅ py_compile/typecheck/lint 通过

---

## 18. 第 7 阶段实施记录（2026-05-28）

第 7 阶段实现了 MCP Tool Preview UI，详见 [`PHASE_7_MCP_TOOL_PREVIEW_UI_REPORT.md`](./PHASE_7_MCP_TOOL_PREVIEW_UI_REPORT.md)。

**实际实施范围**：

- ✅ 后端新增 `build_mcp_preview()` 构建结构化预览
- ✅ endpoint 返回 `mcp_preview` 替代 `mcp_result`
- ✅ 前端渲染 MCP Tool Preview 区块（工具名、状态、adapter、items、安全提示）
- ✅ 不展示 raw JSON / secret
- ✅ standard chat 模式不受影响
- ✅ py_compile/typecheck/lint 通过

---

## 19. 第 7.5 阶段验证记录（2026-05-28）

第 7.5 阶段验证了 MCP Tool Preview API contract 和安全性，详见 [`PHASE_7_5_MCP_TOOL_PREVIEW_VALIDATION_REPORT.md`](./PHASE_7_5_MCP_TOOL_PREVIEW_VALIDATION_REPORT.md)。

**验证结果**：

- ✅ mcp_preview contract 稳定（所有必需字段存在）
- ✅ mcp_result 已从响应中移除
- ✅ standard prompt-response 不受影响
- ✅ 不展示 raw JSON / secret
- ✅ metadata 字段白名单正确
- ✅ mock adapter 正常
- ✅ stdio adapter 安全闸门正常
- ✅ 写操作仍硬拒绝
- ✅ 无需代码修复

---

## 20. 第 8.0 阶段调研记录（2026-05-28）

第 8.0 阶段完成了 AI/MCP audit logging 调研，详见 [`PHASE_8_0_AUDIT_LOGGING_RESEARCH.md`](./PHASE_8_0_AUDIT_LOGGING_RESEARCH.md)。

**调研结论**：

- ✅ Plane 现有 `IssueActivity`（issue-scoped）、`APIActivityLog`（API 请求）、`RequestLoggerMiddleware`
- ✅ 没有通用 AuditLog model
- ✅ 推荐方案 B：Python logger 结构化安全日志（不需要 migration）
- ✅ 定义了 audit event schema（字段白名单 + 禁止记录字段）
- ✅ 可进入 Phase 8.1 实现

---

## 21. 第 8.1 阶段实施记录（2026-05-28）

第 8.1 阶段实现了最小 AI/MCP audit logging，详见 [`PHASE_8_1_MINIMAL_AUDIT_LOGGING_REPORT.md`](./PHASE_8_1_MINIMAL_AUDIT_LOGGING_REPORT.md)。

**实际实施范围**：

- ✅ 新增 `apps/api/plane/ai/audit_logger.py`（`plane.ai.audit` logger）
- ✅ endpoint 记录 `ai.request`、`ai.request.success`、`ai.request.error`
- ✅ endpoint 记录 MCP tool-level 事件（`ai.tool.call`、`ai.tool.error`）
- ✅ mcp_runtime 记录 `ai.tool.blocked`、`ai.tool.rejected`
- ✅ 只记录 prompt_length，不记录 raw prompt
- ✅ 只记录 item_count，不记录 raw result
- ✅ 错误使用 error_code，不记录 raw exception
- ✅ 不记录 secret / headers / stack trace / env
- ✅ 不改变 API contract
- ✅ py_compile 通过

---

## 22. 第 8.2 阶段验证记录（2026-05-28）

第 8.2 阶段验证了 audit logging 安全性，详见 [`PHASE_8_2_AUDIT_LOGGING_VALIDATION_REPORT.md`](./PHASE_8_2_AUDIT_LOGGING_VALIDATION_REPORT.md)。

**验证结果**：

- ✅ 不记录 raw prompt / raw result / raw MCP result
- ✅ 不记录 token / API key / cookie / password
- ✅ 不记录 headers / stack trace / env
- ✅ grep 敏感字段检查通过（所有命中均为安全引用）
- ✅ error_code 使用预定义常量
- ✅ API contract 未改变
- ✅ 无需代码修复
