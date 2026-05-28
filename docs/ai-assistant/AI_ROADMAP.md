# AI Assistant Roadmap

> **Phase 2 更新**：本路线图已根据第 1.5 阶段发现的现有 AI 基础设施调整。

## Phase 0: Development Preparation ✅

**Goal**: Set up fork, development environment, documentation, and planning.

**Changes**:

- Fork makeplane/plane
- Clone and configure remotes
- Create branch structure
- Write RFC, security model, architecture docs
- Draft GitHub issue proposal

**Acceptance Criteria**:

- [x] Fork exists at Vme500/plane
- [x] Local clone with correct remotes
- [x] main-ai and feat/ai-phase-0-setup branches
- [x] Documentation complete
- [x] Issue draft ready for review
- [x] Issue submitted: https://github.com/makeplane/plane/issues/9155

**Risks**: None (planning only)

**Future PR**: No (internal preparation)

---

## Phase 1: Code Investigation ✅

**Goal**: Understand Plane codebase structure for AI integration points.

**Changes**:

- Study Plane frontend architecture (React Router SPA, MobX stores)
- Study Plane backend architecture (Django + DRF)
- Identify extension points for AI features
- Document findings

**Acceptance Criteria**:

- [x] Frontend architecture documented
- [x] Backend architecture documented
- [x] Extension points identified
- [x] Database schema analysis complete

**Risks**: Time investment for investigation

**Future PR**: No (investigation only)

---

## Phase 1.5: Existing AI Infrastructure Audit ✅

**Goal**: Verify and document Plane's existing AI infrastructure.

**Changes**:

- Verify pi-chat sidebar entry (exists, no page/route)
- Verify AIService (partially functional)
- Verify backend AI endpoints (exist in external.py)
- Verify has_llm_configured (comes from LLM_API_KEY)
- Document findings

**Acceptance Criteria**:

- [x] pi-chat status verified
- [x] AIService status verified
- [x] Backend endpoints verified
- [x] has_llm_configured source verified
- [x] Research report complete

**Risks**: None (investigation only)

**Future PR**: No (investigation only)

---

## Phase 2: Architecture Decision ✅

**Goal**: Align architecture with existing AI infrastructure.

**Changes**:

- Document architecture decisions based on Phase 1.5 findings
- Define feature flag strategy (enable_ai_assistant, enable_ai_mcp_runtime)
- Define first version minimal scope (simple prompt-response, no MCP)
- Update RFC, architecture, and roadmap documents

**Acceptance Criteria**:

- [x] Architecture decision document complete
- [x] RFC updated to reflect existing infrastructure
- [x] Roadmap updated
- [ ] Feature flag implementation plan finalized

**Risks**: Low (planning only)

**Future PR**: No (planning only)

---

## Phase 3: pi-chat Minimal Page Skeleton ✅

**Goal**: Make `/:workspaceSlug/pi-chat/` route work with a minimal chat page.

**Changes**:

- Add route for `/:workspaceSlug/pi-chat/`
- Create minimal chat page component
- Show "LLM not configured" when `has_llm_configured=false`
- Show chat interface when LLM is configured
- Connect to existing AIService `createGptTask()` for prompt-response
- TODO: gate with `enable_ai_assistant` flag (deferred to Phase 4)

**Acceptance Criteria**:

- [x] `/:workspaceSlug/pi-chat/` route exists
- [x] Page shows "LLM not configured" when `has_llm_configured=false`
- [x] Chat input and message display work
- [x] Connected to existing `/ai-assistant/` endpoint via AIService
- [x] No changes to existing features
- [x] No functional code changes outside pi-chat scope
- [ ] `enable_ai_assistant` flag control (deferred to Phase 4)

**Risks**: Low (new page, no existing code modified)

**Future PR**: Yes (pi-chat page)

**Report**: See [PHASE_3_PI_CHAT_PAGE_REPORT.md](./PHASE_3_PI_CHAT_PAGE_REPORT.md)

---

## Phase 4: Basic Prompt-Response Enhancement ✅

**Goal**: Enhance pi-chat prompt-response and add feature flag.

**Changes**:

- Add `enable_ai_assistant` and `enable_ai_mcp_runtime` feature flags (types + backend)
- Gate pi-chat page with feature flag and LLM configured check
- Optimize response display (remove JSON.stringify fallback)
- Add memory-level conversation history with stable message IDs
- Fix no-array-index-key lint warning

**Acceptance Criteria**:

- [x] `enable_ai_assistant` flag added to IInstanceConfig and /api/instances/
- [x] `enable_ai_mcp_runtime` flag added to IInstanceConfig and /api/instances/
- [x] pi-chat page gated: disabled → not configured → chat
- [x] Response display optimized (extractAIResponse helper)
- [x] Conversation history with stable IDs
- [x] no-array-index-key warning fixed
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Low (feature flags default to false, no existing behavior changed)

**Future PR**: Yes (feature flags + prompt improvements)

**Report**: See [PHASE_4_FEATURE_FLAG_PROMPT_REPORT.md](./PHASE_4_FEATURE_FLAG_PROMPT_REPORT.md)

---

## Phase 5: AI Settings Page ✅

**Goal**: Implement workspace AI settings (read-only).

**Changes**:

- Add "AI Assistant" to Workspace Settings sidebar (FEATURES category)
- Read-only settings page showing AI Assistant status
- Feature flag: `enable_ai_assistant`, `enable_ai_mcp_runtime`, `has_llm_configured`
- No API key display, no save capability

**Acceptance Criteria**:

- [x] AI settings page accessible in Workspace Settings
- [x] Page shows AI Assistant, MCP Runtime, LLM Configuration status
- [x] API key never exposed to frontend
- [x] Page is read-only (no save button)
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Low (read-only page, no backend changes)

**Future PR**: Yes (settings page)

**Report**: See [PHASE_5_AI_SETTINGS_PAGE_REPORT.md](./PHASE_5_AI_SETTINGS_PAGE_REPORT.md)

---

## Phase 6: MCP Runtime (Read-Only) ✅

**Goal**: Add MCP tool calling capability (skeleton with mock implementation).

**Changes**:

- Add MCP runtime module (`apps/api/plane/ai/`)
- Extend endpoint to support `mode=mcp`
- Read-only tools: list_projects, list_work_items, search_work_items, etc.
- Tool call results displayed in chat
- Frontend MCP mode toggle

**Acceptance Criteria**:

- [x] MCP runtime module created
- [x] Read-only tool whitelist defined
- [x] Endpoint supports `mode=mcp` parameter
- [x] Results displayed in structured format
- [x] No write operations allowed
- [x] Frontend MCP mode toggle
- [x] Python py_compile passes
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Medium (mock implementation, not real MCP server)

**Future PR**: Yes (MCP runtime)

**Report**: See [PHASE_6_MCP_READONLY_RUNTIME_REPORT.md](./PHASE_6_MCP_READONLY_RUNTIME_REPORT.md)

---

## Phase 6.6: Permission Hardening ✅

**Goal**: Fix security issues found in Phase 6.5 review.

**Changes**:

- Add workspace membership verification (defense-in-depth)
- Add project membership check for all entity-level tools
- Use `Issue.issue_objects` for automatic archived/draft/triage filtering
- Add return quantity limits on all list/search tools
- Add query length limit on search
- Sanitize error messages (fail-closed, no internals leaked)
- Pass `request.user` object instead of user_id string

**Acceptance Criteria**:

- [x] Cross-workspace data access prevented
- [x] Project membership enforced on all entity tools
- [x] Soft-deleted data filtered (via SoftDeletionManager)
- [x] Archived data filtered per Plane API patterns
- [x] Return quantity limits on all tools
- [x] Safe error messages only
- [x] py_compile passes
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Low (defense-in-depth, follows existing Plane patterns)

**Report**: See [PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md](./PHASE_6_6_MCP_PERMISSION_HARDENING_REPORT.md)

---

## Phase 6.7: Real MCP Server Integration Research ✅

**Goal**: Research and design real plane-mcp-server integration.

**Findings**:

- `plane-mcp-server` available via `uvx plane-mcp-server stdio`
- Requires `PLANE_API_KEY` + `PLANE_WORKSPACE_SLUG` env vars
- stdio transport recommended for Phase 6.8 (subprocess, no Docker changes)
- Auth: workspace-level API key (`X-Api-Key` header), not per-user
- Permission risk: MCP server can access all workspace projects (wider than current user)
- Mitigation: tool allowlist + write operation rejection at client layer
- All 10 read-only tools have matching names in plane-mcp-server

**Risks**: Medium (API key auth bypasses user permissions)

**Report**: See [PHASE_6_7_REAL_MCP_INTEGRATION_RESEARCH.md](./PHASE_6_7_REAL_MCP_INTEGRATION_RESEARCH.md)

---

## Phase 6.8: Real MCP Server stdio Integration (Planned)

**Goal**: Implement stdio adapter to call real plane-mcp-server.

**Planned Changes**:

- Add `AI_MCP_ADAPTER` config (mock|stdio)
- Add `AI_MCP_SERVER_COMMAND` config
- Add `AI_MCP_SERVER_TIMEOUT` config
- Implement stdio MCP client adapter
- Keep mock adapter as fallback
- Tool allowlist secondary filter

**Risks**: Medium (API key auth, subprocess management)

---

## Phase 7: Write Operation Confirmation

**Goal**: Implement confirmation flow for write operations.

**Changes**:

- Add write tools (create, update work items)
- Confirmation dialog before execution
- Parameter review UI
- Execution feedback

**Acceptance Criteria**:

- [ ] Write tools available (behind flag)
- [ ] Confirmation dialog appears before write
- [ ] User can review and approve/reject
- [ ] All write operations logged

**Risks**: Medium (data modification safety)

**Future PR**: Yes (write operations)

---

## Phase 8: Audit Logging

**Goal**: Implement comprehensive audit logging for AI operations.

**Changes**:

- Audit log model (database)
- Log all AI interactions
- Admin audit log viewer
- User interaction history

**Acceptance Criteria**:

- [ ] All AI interactions logged
- [ ] Logs include: user, workspace, tool, params, result, timestamp
- [ ] Sensitive data sanitized in logs
- [ ] Admin can view workspace audit logs

**Risks**: Low (observability feature)

**Future PR**: Yes (audit logging)

---

## Phase 9: Claude Code Runtime (Advanced, Fork-Only)

**Goal**: Implement optional Claude Code Runtime for advanced capabilities.

**Changes**:

- Claude Code Runtime implementation
- Sandboxed execution environment
- Advanced tool support (code analysis, shell, file ops)
- Resource limits and safety controls

**Acceptance Criteria**:

- [ ] Claude Code Runtime available (disabled by default)
- [ ] Runs in sandboxed environment
- [ ] Shell execution allowlisted only
- [ ] Resource limits enforced
- [ ] Can be completely disabled

**Risks**: High (security-sensitive, complex)

**Future PR**: No (fork-only, not for initial official PR)

---

## Phase 10: Docker Packaging

**Goal**: Package AI features for easy deployment.

**Changes**:

- Docker Compose configuration
- Environment variable documentation
- Deployment guide
- Migration scripts

**Acceptance Criteria**:

- [ ] Docker Compose works out of the box
- [ ] All env vars documented
- [ ] Migration scripts tested
- [ ] Backward compatible with existing deployments

**Risks**: Medium (deployment complexity)

**Future PR**: Yes (deployment infrastructure)
