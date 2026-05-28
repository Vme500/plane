# 第 1.5 阶段报告：Plane 现有 AI 基础设施专项核验

> 调研日期：2026-05-28
> 分支：feat/ai-phase-1-research
> 目标：核验 Plane 已有 AI 基础设施的现状、可用性、可复用性。

---

## 1. pi-chat 现状判断

### 1.1 定义位置

| 文件 | 内容 |
|------|------|
| `apps/web/core/components/workspace/sidebar/user-menu.tsx:55-59` | `SIDEBAR_USER_MENU_ITEMS` 中定义 `pi-chat` 项，key=`"pi-chat"`，href=`/${workspaceSlug}/pi-chat/`，Icon=`PiChatLogo` |
| `apps/web/core/components/workspace/sidebar/sidebar-item.tsx:52` | `staticItems` 数组包含 `"pi_chat"` |
| `packages/propel/src/icons/sub-brand/pi-chat.tsx` | `PiChatLogo` SVG 图标组件 |
| `packages/propel/src/icons/registry.ts:90` | 注册 `"sub-brand.pi-chat": PiChatLogo` |

### 1.2 路由位置

**无路由定义。** `apps/web/app/routes/core.ts` 中没有 `pi-chat` 相关路由。

### 1.3 显示条件

**无条件渲染。** `SIDEBAR_USER_MENU_ITEMS` 中的 `pi-chat` 项没有 `enabled` 或 `isVisible` 条件，只要用户菜单渲染就会显示。

### 1.4 是否在 CE 中可见

**是。** 代码位于 `apps/web/core/`（非 `apps/web/ce/`），属于 Community Edition 公共代码。

### 1.5 点击后跳转到哪里

跳转到 `/${workspaceSlug}/pi-chat/`，但该路由不存在，**会显示 404 页面**。

### 1.6 是否已有页面组件

**无。** 搜索 `apps/web` 目录下所有 `page.tsx` 文件，没有找到 `pi-chat` 相关页面。

### 1.7 i18n 支持

**完整。** 19 种语言都有翻译：
- `packages/i18n/locales/{lang}/common.json` — `"pi_chat": "Plane AI"`（或其他语言翻译）
- `packages/i18n/locales/{lang}/navigation.json` — `"pi_chat": "Plane AI"`

### 1.8 路径检测

`apps/web/core/hooks/use-workspace-paths.ts` 中有：
```ts
const isAiPath = pathname.includes(`/${workspaceSlug}/pi-chat`);
```
用于区分 AI 路径和项目路径。

### 1.9 结论

**pi-chat 是一个已规划但未实现的功能入口。** 侧边栏入口、图标、i18n、路径检测都已就绪，但缺少：
- 路由定义
- 页面组件
- 后端 API（已有通用 AI endpoint，但可能需要专门的聊天 API）

---

## 2. AIService 现状判断

### 2.1 共享包 AIService

**文件**：`packages/services/src/ai/ai.service.ts`

```ts
export class AIService extends APIService {
  constructor(BASE_URL?: string) {
    super(BASE_URL || API_BASE_URL);
  }

  async prompt(workspaceSlug: string, data: { prompt: string; task: string }): Promise<any> {
    return this.post(`/api/workspaces/${workspaceSlug}/ai-assistant/`, data)
  }

  async rephraseGrammar(workspaceSlug: string, data: TTaskPayload): Promise<{response: string}> {
    return this.post(`/api/workspaces/${workspaceSlug}/rephrase-grammar/`, data)
  }
}
```

### 2.2 Web 应用 AIService

**文件**：`apps/web/core/services/ai.service.ts`

```ts
export class AIService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async createGptTask(workspaceSlug: string, data: { prompt: string; task: string }): Promise<any> {
    return this.post(`/api/workspaces/${workspaceSlug}/ai-assistant/`, data)
  }

  async performEditorTask(workspaceSlug: string, data: TTaskPayload): Promise<{response: string}> {
    return this.post(`/api/workspaces/${workspaceSlug}/rephrase-grammar/`, data)
  }
}
```

### 2.3 方法对比

| 方法 | 共享包 | Web 应用 | 后端 endpoint | 状态 |
|------|--------|----------|---------------|------|
| `prompt()` / `createGptTask()` | `prompt()` | `createGptTask()` | `/api/workspaces/{slug}/ai-assistant/` | **可用** |
| `rephraseGrammar()` / `performEditorTask()` | `rephraseGrammar()` | `performEditorTask()` | `/api/workspaces/{slug}/rephrase-grammar/` | **不可用（无后端）** |

### 2.4 调用方

| 调用方 | 使用的方法 | 文件 |
|--------|-----------|------|
| `GptAssistantPopover` | `createGptTask()` | `apps/web/core/components/core/modals/gpt-assistant-popover.tsx` |
| `EditorAIMenu` | `performEditorTask()` | `apps/web/ce/components/pages/editor/ai/menu.tsx` |
| `AskPiMenu` | 间接通过 `EditorAIMenu` | `apps/web/ce/components/pages/editor/ai/ask-pi-menu.tsx` |

### 2.5 结论

**AIService 部分可用。** `prompt()` / `createGptTask()` 方法有完整后端支持，可以正常工作。`rephraseGrammar()` / `performEditorTask()` 缺少后端 endpoint，调用会返回错误。

---

## 3. has_llm_configured 来源

### 3.1 类型定义

**文件**：`packages/types/src/instance/base.ts:61`
```ts
has_llm_configured: boolean;
```

### 3.2 后端来源

**文件**：`apps/api/plane/license/api/views/instance.py:153`
```python
data["has_llm_configured"] = bool(LLM_API_KEY)
```

`LLM_API_KEY` 通过 `get_configuration_value()` 获取，优先从数据库读取，回退到环境变量 `os.environ.get("LLM_API_KEY", "")`。

### 3.3 /api/instances/ 返回逻辑

在 `GET /api/instances/` 响应中，`has_llm_configured` 字段表示实例是否配置了 LLM API key。当 `LLM_API_KEY` 非空时为 `True`。

### 3.4 与 OPENAI_API_KEY / GPT_ENGINE 的关系

**已迁移到新的配置体系：**

| 旧变量 | 新变量 | 状态 |
|--------|--------|------|
| `OPENAI_API_KEY` | `LLM_API_KEY` | 废弃 → 新 |
| `OPENAI_API_BASE` | （已移除） | 废弃 |
| `GPT_ENGINE` | `LLM_MODEL` | 废弃 → 新 |

**文件**：`apps/api/plane/utils/instance_config_variables/core.py`
```python
llm_config_variables = [
    {"key": "LLM_API_KEY", "value": os.environ.get("LLM_API_KEY"), "category": "AI", "is_encrypted": True},
    {"key": "LLM_PROVIDER", "value": os.environ.get("LLM_PROVIDER", "openai"), "category": "AI", "is_encrypted": False},
    {"key": "LLM_MODEL", "value": os.environ.get("LLM_MODEL", "gpt-4o-mini"), "category": "AI", "is_encrypted": False},
    {"key": "GPT_ENGINE", "value": os.environ.get("GPT_ENGINE", "gpt-3.5-turbo"), "category": "AI", "is_encrypted": False},  # Deprecated
]
```

### 3.5 前端使用

**文件**：`apps/web/core/components/issues/issue-modal/components/description-editor.tsx:247,266`

```tsx
{issueName && issueName.trim() !== "" && config?.has_llm_configured && (
  <button onClick={handleAutoGenerateDescription}>I'm feeling lucky</button>
)}
{config?.has_llm_configured && projectId && (
  <GptAssistantPopover ... />
)}
```

### 3.6 结论

**`has_llm_configured` 是一个基于 `LLM_API_KEY` 环境变量的功能开关。** 它控制：
- Issue 描述编辑器中的 "I'm feeling lucky" 按钮
- Issue 描述编辑器中的 GPT Assistant 弹出框

**可以扩展为 AI Assistant feature flag**，但语义不同：`has_llm_configured` 表示"是否配置了 LLM API key"，而我们需要的是"是否启用 AI Assistant 功能"。建议新增 `enable_ai_assistant` 字段。

---

## 4. 后端 AI Endpoint 是否真的缺失

### 4.1 结论：**后端 AI endpoint 实际存在**

**文件**：`apps/api/plane/app/urls/external.py`

```python
from plane.app.views import GPTIntegrationEndpoint, WorkspaceGPTIntegrationEndpoint

urlpatterns = [
    path("unsplash/", UnsplashEndpoint.as_view(), name="unsplash"),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/ai-assistant/",
        GPTIntegrationEndpoint.as_view(),
        name="importer",
    ),
    path(
        "workspaces/<str:slug>/ai-assistant/",
        WorkspaceGPTIntegrationEndpoint.as_view(),
        name="importer",
    ),
]
```

### 4.2 Endpoint 详情

**文件**：`apps/api/plane/app/views/external/base.py`

#### GPTIntegrationEndpoint（项目级）
- **路径**：`/api/workspaces/{slug}/projects/{project_id}/ai-assistant/`
- **方法**：POST
- **权限**：`@allow_permission([ROLE.ADMIN, ROLE.MEMBER])`
- **功能**：接收 `task` 和 `prompt`，调用 LLM API 返回响应

#### WorkspaceGPTIntegrationEndpoint（工作区级）
- **路径**：`/api/workspaces/{slug}/ai-assistant/`
- **方法**：POST
- **权限**：`@allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")`
- **功能**：同上，但不需要 project_id

### 4.3 LLM Provider 支持

```python
SUPPORTED_PROVIDERS = {
    "openai": OpenAIProvider,      # gpt-3.5-turbo, gpt-4o-mini, gpt-4o, o1-mini, o1-preview
    "anthropic": AnthropicProvider, # claude-3-5-sonnet, claude-3-haiku, claude-3-opus, ...
    "gemini": GeminiProvider,       # gemini-pro, gemini-1.5-pro-latest, gemini-pro-vision
}
```

使用 OpenAI SDK 统一调用，支持 OpenAI、Anthropic、Gemini 三个 provider。

### 4.4 缺失的 Endpoint

| Endpoint | 状态 |
|----------|------|
| `/api/workspaces/{slug}/ai-assistant/` | **存在** |
| `/api/workspaces/{slug}/projects/{project_id}/ai-assistant/` | **存在** |
| `/api/workspaces/{slug}/rephrase-grammar/` | **缺失** |

### 4.5 结论

**第 1 阶段调研中"后端 AI endpoint 似乎已移除"的判断是错误的。** 后端 AI endpoint 实际存在于 `external.py`，且功能完整。只有 `rephrase-grammar` endpoint 缺失。

---

## 5. 当前 AI Editor 功能是否可用

### 5.1 Editor AI Menu

**文件**：`apps/web/ce/components/pages/editor/ai/menu.tsx`

功能：
- "Ask Pi" — 向 AI 提问，基于选中文本
- 语气调整（Professional / Casual / Default）— 改写文本

### 5.2 可用性分析

| 功能 | 调用的方法 | 后端 endpoint | 状态 |
|------|-----------|---------------|------|
| Ask Pi | `aiService.performEditorTask()` → `POST /rephrase-grammar/` | **缺失** | **不可用** |
| 语气调整 | `aiService.performEditorTask()` → `POST /rephrase-grammar/` | **缺失** | **不可用** |

**但 Ask Pi 菜单中有独立的输入框**（`AskPiMenu` 组件），可能通过其他方式调用 AI。检查发现 `AskPiMenu` 组件本身不直接调用 API，而是通过 `EditorAIMenu` 的 `handleGenerateResponse` 调用 `performEditorTask`。

### 5.3 GptAssistantPopover

**文件**：`apps/web/core/components/core/modals/gpt-assistant-popover.tsx`

功能：在 Issue 描述编辑器中弹出 AI 助手，调用 `aiService.createGptTask()` → `POST /ai-assistant/`。

**状态：可用**（当 `LLM_API_KEY` 已配置时）。

### 5.4 结论

| 组件 | 状态 | 原因 |
|------|------|------|
| GptAssistantPopover（Issue 编辑器） | **可用** | 使用 `/ai-assistant/` endpoint，后端存在 |
| EditorAIMenu（页面编辑器） | **不可用** | 使用 `/rephrase-grammar/` endpoint，后端缺失 |
| AskPiMenu（页面编辑器内） | **不可用** | 依赖 EditorAIMenu 的 API 调用 |

---

## 6. 哪些代码可以复用

### 6.1 高复用性

| 组件 | 路径 | 复用方式 |
|------|------|----------|
| `AIService` | `packages/services/src/ai/ai.service.ts` | 扩展为 MCPAIService，添加聊天和 MCP 工具调用方法 |
| `WorkspaceGPTIntegrationEndpoint` | `apps/api/plane/app/views/external/base.py` | 扩展为 AI Assistant 聊天 endpoint，添加 MCP 工具调用 |
| `has_llm_configured` | `packages/types/src/instance/base.ts` | 参考模式，新增 `enable_ai_assistant` |
| `GptAssistantPopover` | `apps/web/core/components/core/modals/gpt-assistant-popover.tsx` | 参考 UI 模式，改造为 AI 聊天面板 |
| `PiChatLogo` | `packages/propel/src/icons/sub-brand/pi-chat.tsx` | 直接复用图标 |
| `SIDEBAR_USER_MENU_ITEMS` | `apps/web/core/components/workspace/sidebar/user-menu.tsx` | 复用 `pi-chat` 入口 |
| `LLMProvider` 体系 | `apps/api/plane/app/views/external/base.py` | 复用多 provider 支持 |
| `llm_config_variables` | `apps/api/plane/utils/instance_config_variables/core.py` | 扩展 AI 配置变量 |
| i18n 翻译 | `packages/i18n/locales/*/common.json` | 复用 `pi_chat` 翻译 key |

### 6.2 中等复用性

| 组件 | 路径 | 复用方式 |
|------|------|----------|
| `IssueActivity` 模型 | `apps/api/plane/db/models/issue.py` | 参考模式创建 `AIActivity` |
| `APIToken` 模型 | `apps/api/plane/db/models/api.py` | 可用于 AI API 认证 |
| `WorkspaceUserPreference` | `apps/api/plane/db/models/workspace.py` | 可用于 AI 偏好设置 |
| `useWorkspacePaths` | `apps/web/core/hooks/use-workspace-paths.ts` | 扩展 `isAiPath` 检测 |

---

## 7. 哪些代码应避免复用

### 7.1 避免直接复用

| 组件 | 原因 |
|------|------|
| `GPTIntegrationEndpoint` 的 URL 命名 | `name="importer"` 是错误的命名，应使用更语义化的名称 |
| `GPTIntegrationEndpoint` 的权限装饰器 | 使用 `@allow_permission` 装饰器，但 AI Assistant 可能需要更细粒度的权限控制 |
| `rephraseGrammar` 相关代码 | 后端 endpoint 缺失，前端代码已过时 |
| `GPT_ENGINE` 配置变量 | 已废弃，使用 `LLM_MODEL` 替代 |
| `OPENAI_API_BASE` 环境变量 | 已废弃，不再使用 |

### 7.2 避免的模式

| 模式 | 原因 |
|------|------|
| 直接在 `external.py` 中添加新 endpoint | `external.py` 混合了 Unsplash 和 AI 功能，应创建独立的 `ai.py` |
| 复用 `get_llm_response()` 的直接 OpenAI SDK 调用 | AI Assistant 需要 MCP 工具调用，不能直接用简单的 completion |
| 复用 `GptAssistantPopover` 的完整实现 | 它是为简单的 prompt-response 设计的，不支持工具调用和确认流程 |

---

## 8. 对后续路线的建议

### 8.1 复用 pi-chat 还是新增 ai-assistant

**建议：复用 pi-chat 入口，新增 ai-assistant 路由和页面。**

理由：
- `pi-chat` 侧边栏入口已经存在，有完整的 i18n 支持和图标
- 用户已经看到这个入口，删除会造成困惑
- 但 `pi-chat` 这个名称不够通用，建议在 i18n 中将显示名称改为 "AI Assistant"
- 路由可以使用 `/:workspaceSlug/pi-chat/`（复用现有 href）或 `/:workspaceSlug/ai-assistant/`

**具体操作**：
1. 保留 `SIDEBAR_USER_MENU_ITEMS` 中的 `pi-chat` 项
2. 修改 i18n 翻译：`"pi_chat": "AI Assistant"`（英文）
3. 添加路由：`/:workspaceSlug/pi-chat/` → AI 聊天页面
4. 或者将 href 改为 `/:workspaceSlug/ai-assistant/` 并添加新路由

### 8.2 复用 AIService 还是新建 MCPAIService

**建议：扩展现有 AIService，添加 MCP 相关方法。**

理由：
- `AIService` 已经有 `prompt()` 方法可以正常工作
- 后端 `WorkspaceGPTIntegrationEndpoint` 可以扩展支持 MCP 工具调用
- 不需要新建 service 类，避免代码重复

**具体操作**：
1. 在 `packages/services/src/ai/ai.service.ts` 中添加新方法：
   ```ts
   async chat(workspaceSlug: string, data: { message: string; conversation_id?: string }): Promise<AIChatResponse>
   async confirmAction(workspaceSlug: string, data: { action_id: string; confirmed: boolean }): Promise<any>
   async getSettings(workspaceSlug: string): Promise<AISettings>
   async updateSettings(workspaceSlug: string, data: Partial<AISettings>): Promise<AISettings>
   ```
2. 保留现有 `prompt()` 方法的向后兼容性

### 8.3 扩展 has_llm_configured 还是新增 enable_ai_assistant

**建议：新增 `enable_ai_assistant`，保留 `has_llm_configured`。**

理由：
- `has_llm_configured` 语义是"是否配置了 LLM API key"，用于控制 Issue 编辑器的 AI 功能
- `enable_ai_assistant` 语义是"是否启用 AI Assistant 功能"，用于控制侧边栏入口和聊天功能
- 两者可以独立控制：有 API key 不一定启用 Assistant，启用 Assistant 不一定需要 API key（可以使用内置 key）

**具体操作**：
1. 在 `packages/types/src/instance/base.ts` 中添加：
   ```ts
   enable_ai_assistant: boolean;
   enable_ai_mcp_runtime: boolean;
   ```
2. 在 `apps/api/plane/license/api/views/instance.py` 中添加：
   ```python
   data["enable_ai_assistant"] = os.environ.get("ENABLE_AI_ASSISTANT", "0") == "1"
   data["enable_ai_mcp_runtime"] = os.environ.get("ENABLE_AI_MCP_RUNTIME", "0") == "1"
   ```
3. 在 `apps/api/plane/utils/instance_config_variables/core.py` 中添加对应的配置变量

### 8.4 是否需要恢复旧后端 endpoint

**建议：不需要恢复，直接扩展现有 endpoint。**

理由：
- `/api/workspaces/{slug}/ai-assistant/` endpoint 已存在且功能正常
- 只需要扩展 `WorkspaceGPTIntegrationEndpoint` 支持 MCP 工具调用
- `/api/workspaces/{slug}/rephrase-grammar/` 是页面编辑器专用，与 AI Assistant 无关，可以暂不恢复

**具体操作**：
1. 扩展 `WorkspaceGPTIntegrationEndpoint.post()` 方法：
   - 添加 `conversation_id` 参数支持多轮对话
   - 添加 MCP 工具调用逻辑
   - 添加确认机制
2. 新增 GET 方法获取 AI 设置
3. 新增 PUT 方法更新 AI 设置
4. 在 `apps/api/plane/app/urls/external.py` 或新建 `ai.py` 中添加新路由

---

## 9. 附录：完整文件清单

### 9.1 前端 AI 相关文件

| 文件 | 用途 | 状态 |
|------|------|------|
| `packages/services/src/ai/ai.service.ts` | 共享 AIService | 部分可用 |
| `packages/services/src/ai/index.ts` | 导出 | 正常 |
| `apps/web/core/services/ai.service.ts` | Web AIService | 部分可用 |
| `apps/web/core/constants/ai.ts` | AI_EDITOR_TASKS 枚举 | 正常 |
| `apps/web/core/components/core/modals/gpt-assistant-popover.tsx` | GPT 弹出框 | 可用 |
| `apps/web/ce/components/pages/editor/ai/menu.tsx` | 编辑器 AI 菜单 | 不可用 |
| `apps/web/ce/components/pages/editor/ai/ask-pi-menu.tsx` | Ask Pi 菜单 | 不可用 |
| `apps/web/core/components/workspace/sidebar/user-menu.tsx` | 侧边栏 pi-chat 入口 | 存在（无页面） |
| `apps/web/core/components/workspace/sidebar/sidebar-item.tsx` | 侧边栏静态项 | 包含 pi_chat |
| `apps/web/core/hooks/use-workspace-paths.ts` | 路径检测 | 包含 isAiPath |
| `packages/propel/src/icons/sub-brand/pi-chat.tsx` | PiChatLogo 图标 | 正常 |
| `packages/types/src/instance/base.ts` | has_llm_configured 类型 | 正常 |
| `packages/i18n/locales/*/common.json` | pi_chat 翻译 | 完整 |
| `packages/i18n/locales/*/navigation.json` | pi_chat 翻译 | 完整 |

### 9.2 后端 AI 相关文件

| 文件 | 用途 | 状态 |
|------|------|------|
| `apps/api/plane/app/views/external/base.py` | GPTIntegrationEndpoint, WorkspaceGPTIntegrationEndpoint | 可用 |
| `apps/api/plane/app/urls/external.py` | AI endpoint URL 定义 | 可用 |
| `apps/api/plane/app/views/__init__.py` | 导出 GPT 相关 view | 正常 |
| `apps/api/plane/license/api/views/instance.py` | has_llm_configured 设置 | 正常 |
| `apps/api/plane/utils/instance_config_variables/core.py` | LLM 配置变量 | 正常 |

### 9.3 环境变量

| 变量 | 用途 | 状态 |
|------|------|------|
| `LLM_API_KEY` | LLM API 密钥 | 当前使用 |
| `LLM_PROVIDER` | LLM 提供商（openai/anthropic/gemini） | 当前使用 |
| `LLM_MODEL` | LLM 模型名称 | 当前使用 |
| `GPT_ENGINE` | 旧模型变量 | 废弃 |
| `OPENAI_API_KEY` | 旧 API key 变量 | 废弃 |
| `OPENAI_API_BASE` | 旧 API base 变量 | 废弃 |
