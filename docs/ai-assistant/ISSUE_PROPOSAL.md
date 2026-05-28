# Proposal: Feature-flagged AI Assistant integration using Plane MCP Server

## Summary

This issue proposes adding an **optional, feature-flagged, disabled-by-default** AI Assistant to Plane's web UI, leveraging the existing `plane-mcp-server` to provide AI-powered querying and (eventually) management of Plane data directly within the browser.

## Motivation

Plane already has an official MCP server (`plane-mcp-server`) that exposes Plane data via the Model Context Protocol. This enables AI assistants like Claude to interact with Plane—but currently requires external tools (VS Code with Claude extension, Claude Desktop app).

**The gap**: Regular workspace users who don't use VS Code or Claude Desktop cannot benefit from AI assistance within Plane. Integrating an AI Assistant directly into the Plane web UI would:

1. **Lower the barrier** - No additional software installation required
2. **Improve accessibility** - Available to all workspace users in the browser
3. **Leverage existing infrastructure** - Reuse `plane-mcp-server` tools
4. **Maintain security** - Server-side key handling, permission-aware, audit-logged

## Proposed Scope

### In Scope (Initial)
- **Read-only** MCP tools: query projects, work items, states, labels, cycles, modules
- **Feature-flagged**: All AI features behind `ENABLE_AI_ASSISTANT` flag
- **Disabled by default**: Must be explicitly enabled by workspace admin
- **Server-side secrets**: API keys stored and used server-side only
- **Permission-aware**: Respects existing workspace/project/user permissions
- **Audit logging**: All AI interactions logged with sanitized parameters

### Out of Scope (Initial)
- Write operations (create, update, delete work items)
- Arbitrary code execution
- Shell access
- Advanced runtimes are out of scope for this proposal.
- Frontend API key exposure

## Proposed UI Placement

### 1. Left Sidebar
- Add "AI Assistant" entry below "Stickies"
- Clicking opens the AI chat panel
- Only visible when `ENABLE_AI_ASSISTANT=true`

### 2. Workspace Settings
- New "AI Assistant" section
- Configure: API key, provider, model, tool allowlist, project allowlist
- Only accessible to workspace admins

### 3. Personal Settings
- New "AI Preferences" section
- Enable/disable AI for personal account
- Choose preferred model (if workspace allows)

## Architecture Direction

```
Plane UI → Plane Backend AI APIs → AI Runtime / MCP Client → plane-mcp-server → Plane API
```

### Key Design Decisions

1. **Reuse `plane-mcp-server`**: No duplicate API client logic. The AI Runtime acts as an MCP client connecting to the existing MCP server.

2. **MCP Client in Backend**: The MCP client runs server-side in the Plane backend. No MCP connections from the frontend.

3. **Transport**: The MCP transport mechanism can be discussed; the implementation should keep transport details abstract.

4. **Runtime**: A single MCP-based runtime handles tool calls via the MCP protocol. The initial version is read-only.

5. **Feature Flags**:
   ```env
   ENABLE_AI_ASSISTANT=false          # Master switch
   ENABLE_AI_MCP_RUNTIME=false        # MCP Runtime
   ```

## Safety and Permission Model

### Secret Handling
- API keys stored server-side only (encrypted at rest)
- Never returned to frontend in plaintext
- Sanitized in all logs
- Not included in configuration exports

### Permission Model
- AI respects existing workspace/project/user permissions
- AI cannot perform actions the user couldn't do manually
- Tool allowlist restricts which MCP tools are available
- Project allowlist restricts which projects AI can access

### Tool Safety
- Read-only tools allowed by default
- Future write operations, if accepted, should require explicit user confirmation
- Destructive operations (delete) disabled by default
- All tool calls logged with sanitized parameters

### Audit
- Every AI interaction logged: user, workspace, project, tool, parameters, result, error, timestamp, confirmation status
- Logs queryable by workspace admins
- Users can view their own interaction history

## Open Questions

1. **MCP Server Bundling**: Should `plane-mcp-server` be bundled with the Plane Docker image, or deployed as a separate service?

2. **AI Provider Support**: Should we support multiple AI providers (Claude, OpenAI, etc.) from the start, or begin with one?

3. **Rate Limiting**: What rate limits should apply per user and per workspace?

4. **Cost Control**: How should we handle AI API cost management? Per-workspace limits? Usage alerts?

5. **Conversation Storage**: Should conversation history be stored in the database, or session-only?

6. **Streaming Responses**: Should the chat support streaming (token-by-token) responses?

7. **Tool Result Caching**: Should we cache common query results to reduce API calls?

## Implementation Approach

### Phase 0: Development Preparation (Current)
- Fork, clone, branch structure
- Documentation and planning
- Issue discussion

### Phase 1-2: Investigation and Infrastructure
- Code investigation
- Feature flag infrastructure
- Configuration models

### Phase 3-4: UI and Settings
- UI skeleton
- AI settings page
- Key storage

### Phase 5-6: Core AI
- MCP Runtime (read-only)
- Chat panel
- Tool call display

### Phase 7-8: Safety and Observability
- Write operation confirmation (if write operations are accepted in the future)
- Audit logging

### Phase 9: Advanced Runtime (Optional)
- Advanced runtimes are out of scope for this proposal.
- **Not proposed for initial official PR**

### Phase 10: Deployment
- Docker packaging
- Documentation

## Notes

- This proposal is for discussion. No code changes are being proposed yet.
- The approach prioritizes **safety** (feature-flagged, disabled by default, read-only first) and **modularity** (reusing existing MCP server).
- Advanced runtimes are out of scope for this proposal.
- The goal is to contribute a **safe, optional, well-documented** AI integration that enhances Plane without compromising its security or stability.
