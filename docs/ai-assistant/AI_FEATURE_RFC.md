# AI Feature RFC: Plane AI MCP Assistant

## 1. Background

Plane has an official [plane-mcp-server](https://github.com/makeplane/plane-mcp-server) that exposes Plane data via the Model Context Protocol (MCP). This enables AI assistants like Claude to query and interact with Plane work items through MCP tools.

Currently, using AI with Plane requires external tools (e.g., VS Code with Claude extension, Claude Desktop). This RFC proposes integrating an AI Assistant directly into the Plane web UI, so that any workspace user—without installing additional software—can use AI to query and manage their Plane data.

## 2. Product Goals

### 2.1 Workspace AI Assistant
- A chat-based AI assistant accessible from within the Plane UI.
- Users can ask questions about their projects, work items, cycles, modules, and labels.

### 2.2 AI Settings Page
- Workspace-level AI configuration (admin only).
- Personal AI preferences (per user).
- API key management (server-side only).

### 2.3 AI Chat Panel
- Sidebar or modal-based chat interface.
- Displays tool call results in a structured format.
- Supports conversation history within a session.

### 2.4 MCP Tool Calling
- The AI assistant uses plane-mcp-server tools to query Plane data.
- Tool calls are executed server-side through the AI Runtime.

### 2.5 Write Operation Confirmation
- Any write operation (create, update, delete) requires explicit user confirmation before execution.
- Confirmation dialog shows the exact operation and parameters.

### 2.6 Audit Logging
- All AI interactions are logged: user, workspace, project, tool, sanitized parameters, result, error, timestamp, confirmation status.

### 2.7 Multi-Model Support
- Configurable AI provider (Claude, OpenAI, etc.).
- Model selection per workspace or per user.

### 2.8 Advanced Claude Code Runtime (Fork Only)
- An optional, advanced runtime inspired by Claude Code.
- Provides capabilities like code analysis, shell execution, file operations.
- **Disabled by default** and only available in the fork.
- Not proposed for the initial official PR.

## 3. UI Placement

### 3.1 Left Sidebar — Reuse Existing pi-chat Entry
- **复用** `SIDEBAR_USER_MENU_ITEMS` 中已有的 `pi-chat` 项（`apps/web/core/components/workspace/sidebar/user-menu.tsx`）
- 复用 `PiChatLogo` 图标
- 复用 `sidebar.pi_chat` i18n key
- 复用 href `/${workspaceSlug}/pi-chat/`
- 为该路由添加页面组件（当前返回 404）

### 3.2 Workspace Settings
- New "AI Assistant" section in Workspace Settings.
- Configure API keys, enabled features, tool allowlists, project allowlists.

### 3.3 Personal Settings
- New "AI Preferences" section in user settings.
- Choose preferred model, enable/disable AI features for personal account.

## 4. Architecture

> **更新（Phase 2）**：后端 AI endpoint 实际已存在于 `apps/api/plane/app/urls/external.py`，无需从零新建。

```
┌─────────────────────────────────────────────────────────┐
│  Plane UI — pi-chat page (复用现有入口)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ AI Chat Panel│  │ AI Settings  │  │AI Preferences │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘ │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                  Plane Backend                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Existing AI Endpoints (扩展)                     │  │
│  │  /api/workspaces/{slug}/ai-assistant/            │  │
│  │  WorkspaceGPTIntegrationEndpoint                 │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐  │
│  │           AI Runtime / MCP Client (新增)          │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │ Simple MCP Agent Runtime (第一版)            │ │  │
│  │  │ Claude Code Runtime (fork-only, 后置)       │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └───────────────────┼──────────────────────────────┘  │
└──────────────────────┼──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              plane-mcp-server                           │
│  (stdio or HTTP/SSE transport)                          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Plane API (现有)                        │
└─────────────────────────────────────────────────────────┘
```

## 5. Runtime Layering

### 5.1 Simple MCP Agent Runtime
- Default runtime for the AI Assistant.
- Connects to plane-mcp-server via stdio or HTTP/SSE.
- Executes MCP tool calls based on user queries.
- Returns structured results to the chat panel.
- **This is the primary runtime for the initial implementation.**

> **Phase 2 更新**：第一版本不接 MCP，直接使用现有 `/ai-assistant/` endpoint 做简单 prompt-response。MCP 接入在页面和基本 prompt-response 跑通之后。

### 5.2 Claude Code Runtime / Claude-Code-like Runtime
- An advanced runtime inspired by Claude Code capabilities.
- Can analyze code, execute shell commands, perform file operations.
- **Disabled by default.**
- Requires explicit enablement at workspace level.
- Must run in a sandboxed environment.
- **Not part of the initial official PR scope.**

### 5.3 Default State
- All advanced runtimes are disabled by default.
- Only the Simple MCP Agent Runtime is enabled when AI Assistant is turned on.

## 6. Feature Flags

```env
# Master switch for AI Assistant
ENABLE_AI_ASSISTANT=false

# Enable MCP Runtime (Simple MCP Agent)
ENABLE_AI_MCP_RUNTIME=false

# Enable Claude Code Runtime (advanced, fork-only)
ENABLE_AI_CLAUDE_CODE_RUNTIME=false
```

- `ENABLE_AI_ASSISTANT`: Master switch. When false, all AI features are hidden.
- `ENABLE_AI_MCP_RUNTIME`: Enables the Simple MCP Agent Runtime. Requires `ENABLE_AI_ASSISTANT=true`.
- `ENABLE_AI_CLAUDE_CODE_RUNTIME`: Enables the advanced Claude Code Runtime. Requires `ENABLE_AI_ASSISTANT=true`. **Fork-only feature.**

## 7. First Version Scope

### 7.1 Read-Only Tools
The initial version supports only read operations:

| Tool | Description |
|------|-------------|
| `get_me` | Get current user info |
| `list_projects` | List all projects in workspace |
| `retrieve_project` | Get project details |
| `list_work_items` | List work items with filters |
| `search_work_items` | Search work items by query |
| `retrieve_work_item` | Get work item details |
| `list_states` | List workflow states |
| `list_labels` | List labels |
| `list_cycles` | List cycles |
| `list_modules` | List modules |

### 7.2 Safety Constraints
- No delete operations in v1.
- No bulk operations in v1.
- Write operations require explicit confirmation (planned for v2).
- All operations respect existing Plane permissions.

### 7.3 What's NOT in v1
- Arbitrary shell execution.
- Claude Code Runtime enabled by default.
- Bypassing Plane workspace/project/user permissions.
- API key exposure to the frontend.

## 8. Non-Goals

- **Not** embedding Claude Code directly into Plane in v1.
- **Not** enabling advanced runtimes by default.
- **Not** bypassing Plane's existing permission model.
- **Not** exposing API keys or secrets to the frontend.
- **Not** supporting arbitrary code execution in v1.

## 9. Future Considerations

- Write operations with confirmation (Phase 7).
- Audit logging (Phase 8).
- Claude Code Runtime as optional advanced feature (Phase 9).
- Docker packaging with AI features (Phase 10).
- Contributing modular, safe, feature-flagged parts back to official Plane.
