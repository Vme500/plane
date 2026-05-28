# AI Security Model

## 1. Secret Handling

### 1.1 API Key Storage
- AI provider API keys (e.g., Anthropic, OpenAI) are stored **server-side only**.
- Keys are stored in the database, encrypted at rest.
- Keys are never returned to the frontend in plaintext.
- The settings UI shows masked values (e.g., `sk-ant-...****...`).

### 1.2 Log Sanitization
- All AI interaction logs sanitize sensitive parameters.
- API keys, tokens, and credentials are replaced with `[REDACTED]` in logs.
- User content that may contain secrets is sanitized before logging.

### 1.3 Configuration Export
- Configuration export/import does **not** include API keys.
- Keys must be re-entered after importing configuration.

### 1.4 Environment Variables
- `.env` files containing secrets are not committed to Git.
- `.env.example` files use placeholder values only.
- Git pre-commit hooks check for secret patterns.

## 2. Permission Model

### 2.1 Workspace Permissions
- AI Assistant respects existing workspace role permissions.
- A viewer cannot use AI to perform actions they couldn't do manually.
- AI operations are scoped to the current user's workspace access.

### 2.2 Project Permissions
- AI can only access projects the user has permission to view.
- Project allowlists can further restrict AI access (admin configurable).

### 2.3 User Permissions
- Individual users can disable AI features in their personal settings.
- AI does not escalate user privileges.

### 2.4 Principle of Least Privilege
- AI Runtime operates with the minimum permissions required.
- No service-level or admin-level API keys for user-facing operations.

## 3. Tool Safety

### 3.1 Read-Only Default
- Read-only tools are allowed by default when AI is enabled.
- No configuration required for read operations.

### 3.2 Write Operation Confirmation
- Write operations (create, update) require explicit user confirmation.
- Confirmation dialog shows:
  - Tool name
  - Operation description
  - Parameters (sanitized)
  - Target resource
- User must click "Confirm" before execution.

### 3.3 Destructive Operation Restrictions
- Delete operations are **disabled by default**.
- Bulk destructive operations are **never allowed** in v1.
- If enabled in future versions, destructive ops require double confirmation.

### 3.4 Tool Allowlist
- Administrators can configure which MCP tools are available.
- Only tools on the allowlist can be invoked by the AI.
- Default allowlist includes only read-only tools.

### 3.5 Project Allowlist
- Administrators can restrict AI access to specific projects.
- Projects not on the allowlist are invisible to the AI.

## 4. Audit Logging

### 4.1 Logged Information
Every AI interaction is logged with:
- `timestamp`: ISO 8601 timestamp
- `user_id`: ID of the user who initiated the interaction
- `workspace_id`: Workspace context
- `project_id`: Project context (if applicable)
- `tool_name`: MCP tool invoked
- `parameters`: Sanitized tool parameters (secrets redacted)
- `result_summary`: Summary of the tool result
- `error`: Error message (if any)
- `confirmed`: Whether the user confirmed the operation
- `model`: AI model used
- `runtime`: Runtime used (simple MCP, Claude Code, etc.)

### 4.2 Log Storage
- Audit logs are stored in the database.
- Logs are queryable by workspace admins.
- Logs are retained according to workspace retention policy.

### 4.3 Log Access
- Workspace admins can view AI audit logs.
- Users can view their own AI interaction history.
- Logs are not exposed via the AI chat interface itself.

## 5. Claude Code Runtime Risk Assessment

### 5.1 Default State
- Claude Code Runtime is **disabled by default**.
- Must be explicitly enabled at workspace level.
- Feature flag: `ENABLE_AI_CLAUDE_CODE_RUNTIME=false`

### 5.2 Sandboxing Requirements
If enabled, Claude Code Runtime must:
- Run in an isolated container or sandbox.
- Not have access to the host filesystem by default.
- Not have network access beyond what's required.
- Have resource limits (CPU, memory, disk, time).

### 5.3 Shell Execution
- Shell execution is **not allowed by default**.
- If enabled, must be in a sandboxed environment.
- Commands must be allowlisted.
- All shell interactions are logged.

### 5.4 Scope Limitation
- Claude Code Runtime is a **fork-only feature**.
- Not proposed for the initial official PR.
- Not enabled in production deployments by default.
- Intended for advanced users who understand the risks.

## 6. Network Security

### 6.1 API Communication
- All API communication uses HTTPS.
- AI provider API calls are made server-side only.
- No direct frontend-to-AI-provider communication.

### 6.2 Proxy Environment
- Self-hosted deployments may use HTTP proxies.
- Proxy configuration must be supported for AI API calls.
- `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY` environment variables are respected.

### 6.3 Rate Limiting
- AI API calls are rate-limited per user and per workspace.
- Prevents abuse and controls costs.

## 7. Data Privacy

### 7.1 Data Sent to AI Providers
- Only the user's query and necessary context are sent to the AI provider.
- No bulk data export to AI providers.
- Users are informed that their queries are processed by a third-party AI service.

### 7.2 Data Retention
- AI conversation history is stored locally in the Plane instance.
- Conversation history is not sent to AI providers for training.
- Users can clear their conversation history.

### 7.3 Compliance
- AI features respect existing workspace data residency requirements.
- AI features can be completely disabled for compliance-sensitive workspaces.
