# AI MCP Architecture

> **Phase 2 更新**：后端 AI endpoint 实际已存在于 `apps/api/plane/app/urls/external.py`（`WorkspaceGPTIntegrationEndpoint` 和 `GPTIntegrationEndpoint`）。本架构方案基于现有 endpoint 增量扩展，而非从零新建。

## 1. Why Reuse plane-mcp-server

### 1.1 Existing Implementation
Plane already maintains [plane-mcp-server](https://github.com/makeplane/plane-mcp-server), which provides:
- MCP tool definitions for Plane operations.
- Authentication via API tokens.
- Standard MCP protocol compliance.

### 1.2 Benefits of Reuse
- **No duplicate logic**: Avoid reimplementing API client code.
- **Upstream updates**: Benefit from official plane-mcp-server improvements.
- **Consistency**: Same tool definitions as external MCP clients (Claude Desktop, VS Code).
- **Reduced maintenance**: One MCP server implementation to maintain.

### 1.3 Integration Approach
- The AI Runtime in Plane backend acts as an MCP **client**.
- It connects to plane-mcp-server as the MCP **server**.
- Communication follows the standard MCP protocol.

## 2. Supported Transports

### 2.1 stdio Transport
- plane-mcp-server runs as a subprocess.
- Communication via stdin/stdout.
- Lower latency, no network overhead.
- **Recommended for self-hosted deployments.**

### 2.2 HTTP/SSE Transport
- plane-mcp-server runs as a separate HTTP service.
- Communication via Server-Sent Events (SSE) or streamable HTTP.
- Better for containerized deployments.
- Supports remote MCP server deployment.

### 2.3 Transport Selection
- Configurable via `AI_MCP_TRANSPORT` environment variable.
- Default: `stdio` for simplicity.
- `http` for containerized or remote deployments.

## 3. MCP Client Placement

### 3.1 Location
The MCP client resides in the Plane backend:
```
plane/backend/
  plane/
    ai/
      mcp_client.py        # MCP client implementation
      runtime.py            # AI Runtime orchestration
      tools.py              # Tool definitions and safety checks
      views.py              # API endpoints
      models.py             # Database models
      serializers.py        # API serializers
```

### 3.2 Responsibilities
- **MCP Client**: Manages connection to plane-mcp-server, sends tool calls, receives results.
- **Runtime**: Orchestrates the AI conversation loop (query → AI model → tool calls → results → response).
- **Tools**: Defines tool allowlists, safety checks, confirmation logic.
- **Views**: Exposes REST API endpoints for the frontend.

### 3.3 AI Agent Service
- The "AI agent" is a component within the Plane backend, not a separate service.
- It uses the existing Plane backend infrastructure (Django, Celery, etc.).
- No additional microservice required for v1.

## 4. Relationship to Plane Backend

### 4.1 Shared Infrastructure
- Uses existing Django models and ORM.
- Uses existing authentication and authorization.
- Uses existing database (PostgreSQL).
- Uses existing task queue (Celery) for async operations.

### 4.2 API Endpoints

**现有 endpoint（复用）**：
```
POST /api/workspaces/{slug}/ai-assistant/                    # WorkspaceGPTIntegrationEndpoint
POST /api/workspaces/{slug}/projects/{project_id}/ai-assistant/  # GPTIntegrationEndpoint
```

**新增 endpoint（后续扩展）**：
```
GET  /api/workspaces/{slug}/ai/settings/    # 获取 AI 设置
PUT  /api/workspaces/{slug}/ai/settings/    # 更新 AI 设置
POST /api/workspaces/{slug}/ai/chat/        # 聊天（扩展 mode 参数支持 MCP）
POST /api/workspaces/{slug}/ai/confirm/     # 确认写操作
GET  /api/workspaces/{slug}/ai/history/     # 对话历史
```

### 4.3 Data Flow
```
1. User sends message via Plane UI
2. Frontend calls POST /api/ai/chat
3. Backend AI Runtime:
   a. Sends user message to AI model (Claude, GPT, etc.)
   b. AI model returns tool_use response
   c. Runtime checks tool safety (allowlist, permissions)
   d. If write operation: returns confirmation request to frontend
   e. If confirmed: executes tool via MCP client
   f. Returns result to AI model for final response
4. Backend returns response to frontend
```

## 5. Self-Hosted Deployment Configuration

### 5.1 Required Environment Variables
```env
# Plane instance URL (used by MCP server to connect to Plane API)
PLANE_BASE_URL=https://plane.example.com

# Workspace slug
PLANE_WORKSPACE_SLUG=my-workspace

# Plane API token (for MCP server authentication)
PLANE_API_KEY=plane_api_xxxxx

# AI provider configuration
AI_PROVIDER=anthropic  # or openai
AI_API_KEY=sk-ant-xxxxx  # stored server-side only
AI_MODEL=claude-sonnet-4-20250514

# MCP transport configuration
AI_MCP_TRANSPORT=stdio  # or http
AI_MCP_SERVER_PATH=/path/to/plane-mcp-server  # for stdio
AI_MCP_SERVER_URL=http://localhost:3100  # for http
```

### 5.2 Docker Compose Example
```yaml
services:
  plane-backend:
    environment:
      - ENABLE_AI_ASSISTANT=true
      - ENABLE_AI_MCP_RUNTIME=true
      - AI_PROVIDER=anthropic
      - AI_API_KEY=${ANTHROPIC_API_KEY}
      - AI_MCP_TRANSPORT=stdio
      - PLANE_BASE_URL=http://plane-backend:8000
      - PLANE_WORKSPACE_SLUG=${WORKSPACE_SLUG}
      - PLANE_API_KEY=${PLANE_API_KEY}

  # Optional: separate MCP server container
  plane-mcp-server:
    image: makeplane/plane-mcp-server:latest
    environment:
      - PLANE_BASE_URL=http://plane-backend:8000
      - PLANE_WORKSPACE_SLUG=${WORKSPACE_SLUG}
      - PLANE_API_KEY=${PLANE_API_KEY}
```

### 5.3 Minimal Configuration
For the simplest setup:
1. Set `ENABLE_AI_ASSISTANT=true`
2. Set `AI_API_KEY` (your Anthropic/OpenAI key)
3. Set `PLANE_API_KEY` (a Plane API token with appropriate permissions)
4. The MCP server is bundled and runs via stdio by default.

## 6. First Version Tool Allowlist

### 6.1 Read-Only Tools (v1)
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_me` | Get current user info | None |
| `list_projects` | List workspace projects | `per_page`, `cursor` |
| `retrieve_project` | Get project details | `project_id` |
| `list_work_items` | List work items | `project_id`, `per_page`, `cursor`, `state`, `priority`, `labels` |
| `search_work_items` | Search work items | `project_id`, `query` |
| `retrieve_work_item` | Get work item details | `project_id`, `work_item_id` |
| `list_states` | List workflow states | `project_id` |
| `list_labels` | List labels | `project_id` |
| `list_cycles` | List cycles | `project_id` |
| `list_modules` | List modules | `project_id` |

### 6.2 Write Operations (Phase 2 - Not in v1)
| Tool | Description | Risk Level |
|------|-------------|------------|
| `create_work_item` | Create a new work item | Medium |
| `update_work_item` | Update work item fields | Medium |
| `create_work_item_comment` | Add a comment | Low |
| `add_work_item_to_cycle` | Assign to cycle | Low |
| `add_work_item_to_module` | Assign to module | Low |

### 6.3 Destructive Operations (Future - Default Disabled)
| Tool | Description | Risk Level |
|------|-------------|------------|
| `delete_work_item` | Delete a work item | High |
| `bulk_update` | Bulk update work items | High |

## 7. Risks and Mitigations

### 7.1 MCP Server Version Compatibility
- **Risk**: plane-mcp-server may not be compatible with all Plane self-hosted versions.
- **Mitigation**: Document supported versions. Test with common self-hosted versions.

### 7.2 API Path and Permission Issues
- **Risk**: 404 errors or permission denied when MCP server calls Plane API.
- **Mitigation**: Use workspace-scoped API tokens. Test common error paths.

### 7.3 Proxy Environment Issues
- **Risk**: Self-hosted instances behind proxies may have connectivity issues.
- **Mitigation**: Support `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` environment variables.

### 7.4 API Token Permissions
- **Risk**: API token may have insufficient permissions for some operations.
- **Mitigation**: Document required token scopes. Validate token on startup.

### 7.5 Rate Limiting
- **Risk**: AI API rate limits may be exceeded.
- **Mitigation**: Implement per-user and per-workspace rate limiting. Cache common queries.

### 7.6 Cost Control
- **Risk**: AI API costs may be unpredictable.
- **Mitigation**: Set per-workspace usage limits. Log all API calls for cost tracking.
