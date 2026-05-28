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
