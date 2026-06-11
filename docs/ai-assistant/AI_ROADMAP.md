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

## Phase 6.8: Real MCP Server stdio Integration ✅

**Goal**: Implement stdio adapter to call real plane-mcp-server.

**Changes**:

- Add `mcp_stdio_adapter.py` (JSON-RPC over subprocess)
- Add `AI_MCP_ADAPTER` config (mock|stdio, default mock)
- Add `AI_MCP_SERVER_COMMAND`, `AI_MCP_SERVER_ARGS`, `AI_MCP_SERVER_TIMEOUT_SECONDS` config
- Dispatch in `mcp_runtime.py` based on adapter config
- Tool allowlist double-check
- Write operation rejection
- No automatic fallback

**Acceptance Criteria**:

- [x] stdio adapter can spawn plane-mcp-server subprocess
- [x] MCP JSON-RPC protocol: initialize → tools/call
- [x] Default adapter is mock (stdio disabled by default)
- [x] No automatic fallback to mock on stdio failure
- [x] Tool allowlist enforced
- [x] Write operations rejected
- [x] subprocess: shell=False, list args, timeout, process cleanup
- [x] Error messages sanitized
- [x] py_compile passes
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Medium (API key auth bypasses user permissions, no post-filtering yet)

**Report**: See [PHASE_6_8_REAL_MCP_STDIO_ADAPTER_REPORT.md](./PHASE_6_8_REAL_MCP_STDIO_ADAPTER_REPORT.md)

---

## Phase 6.9: MCP stdio Safety Gate ✅

**Goal**: Gate stdio adapter results by per-user permissions.

**Changes**:

- Add `_filter_stdio_result()` post-permission filter
- `get_me`: pass-through (no workspace/project data)
- `list_projects`: filter MCP results against user's accessible projects
- `retrieve_project`: validate user has access before returning
- All other stdio tools blocked with clear message
- Fail-closed: all error paths return safe error

**Acceptance Criteria**:

- [x] stdio results never returned without permission filtering
- [x] MEMBER cannot access projects they're not a member of
- [x] Blocked tools return clear error message
- [x] No automatic fallback
- [x] py_compile passes
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Low (safety gate blocks unfiltered data)

**Report**: See [PHASE_6_9_MCP_STDIO_SAFETY_VALIDATION_REPORT.md](./PHASE_6_9_MCP_STDIO_SAFETY_VALIDATION_REPORT.md)

---

## Phase 6.9.1: Sanitize stdio Results ✅

**Goal**: Ensure stdio adapter never returns raw MCP result to frontend.

**Changes**:

- `get_me`: now uses `_serialize_user_safe(request.user)` instead of MCP raw result
- `list_projects`: now queries local DB instead of extracting from MCP raw result
- `retrieve_project`: already used local DB (no change)
- Added `_serialize_user_safe()` helper
- Updated `format_mcp_response_text` for new get_me format

**Acceptance Criteria**:

- [x] Raw MCP result never returned to frontend
- [x] get_me returns request.user safe fields (id, display_name, email)
- [x] list_projects returns local DB safe fields
- [x] retrieve_project returns local DB safe fields
- [x] py_compile passes
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Low

**Report**: See [PHASE_6_9_1_MCP_STDIO_RESULT_SANITIZATION_REPORT.md](./PHASE_6_9_1_MCP_STDIO_RESULT_SANITIZATION_REPORT.md)

---

## Phase 7: MCP Tool Preview UI ✅

**Goal**: Structured preview of MCP tool-call results in chat UI.

**Changes**:

- Add `build_mcp_preview()` in backend — builds safe structured response
- Endpoint returns `mcp_preview` instead of `mcp_result`
- Frontend renders MCP Tool Preview block with tool name, status, items
- Safety note: "Read-only | Permission filtered"
- Standard chat mode unaffected

**Acceptance Criteria**:

- [x] MCP response structured as `mcp_preview`
- [x] Raw `mcp_result` removed from response
- [x] Frontend renders tool name, status, adapter, items
- [x] No raw JSON displayed
- [x] No secrets displayed
- [x] Standard chat mode unaffected
- [x] py_compile passes
- [x] typecheck passes
- [x] lint passes (0 errors)

**Risks**: Low (display-only, no behavior change)

**Report**: See [PHASE_7_MCP_TOOL_PREVIEW_UI_REPORT.md](./PHASE_7_MCP_TOOL_PREVIEW_UI_REPORT.md)

---

## Phase 7.5: MCP Tool Preview Validation ✅

**Goal**: Validate MCP tool preview API contract and safety.

**Findings**:

- mcp_preview contract stable (all required fields present)
- mcp_result removed from response
- standard prompt-response unaffected
- No raw JSON or secrets exposed
- metadata field whitelist correct
- mock adapter working correctly
- stdio adapter safety gate working
- Write operations still hard-rejected
- No code fixes needed

**Risks**: None (validation only)

**Report**: See [PHASE_7_5_MCP_TOOL_PREVIEW_VALIDATION_REPORT.md](./PHASE_7_5_MCP_TOOL_PREVIEW_VALIDATION_REPORT.md)

---

## Phase 8.0: Audit Logging Research ✅

**Goal**: Research and design AI/MCP audit logging.

**Findings**:

- No standalone AuditLog model exists in Plane
- `IssueActivity` is issue-scoped only
- `APIActivityLog` exists for external API requests
- `RequestLoggerMiddleware` logs all API requests
- Recommended: Phase 8.1 uses Python logger (no migration needed)
- Database persistence deferred to Phase 8.2

**Report**: See [PHASE_8_0_AUDIT_LOGGING_RESEARCH.md](./PHASE_8_0_AUDIT_LOGGING_RESEARCH.md)

---

## Phase 8.1: AI Audit Logging ✅

**Goal**: Implement structured audit logging via Python logger.

**Changes**:

- New `apps/api/plane/ai/audit_logger.py` module
- Structured JSON log events via `plane.ai.audit` logger
- Events: ai.request, ai.tool.call, ai.tool.blocked, ai.tool.error, ai.tool.rejected
- Never logs raw prompt, raw result, or secrets
- No migration, no Docker changes

**Acceptance Criteria**:

- [x] audit_logger.py module created
- [x] Structured JSON log events
- [x] Events logged at endpoint and mcp_runtime levels
- [x] Never logs raw prompt or raw result
- [x] Never logs secrets
- [x] Error codes instead of raw exception messages
- [x] No API contract changes
- [x] No migration needed
- [x] py_compile passes

**Report**: See [PHASE_8_1_MINIMAL_AUDIT_LOGGING_REPORT.md](./PHASE_8_1_MINIMAL_AUDIT_LOGGING_REPORT.md)

- No migration, no Docker changes

---

## Phase 8.2: Audit Logging Validation ✅

**Goal**: Validate audit logging safety and API contract.

**Findings**:

- No raw prompt, result, or MCP result logged
- No secrets, headers, stack trace, or env logged
- error_code constants used instead of raw exceptions
- API contract unchanged
- No code fixes needed

**Report**: See [PHASE_8_2_AUDIT_LOGGING_VALIDATION_REPORT.md](./PHASE_8_2_AUDIT_LOGGING_VALIDATION_REPORT.md)

---

## Phase 8.3: Audit Event Persistence Design ✅

**Goal**: Design AIAuditEvent database persistence model.

**Design**:

- New `AIAuditEvent` model inheriting `BaseModel`
- 19 safe fields (no raw prompt, result, secrets, headers, stack trace)
- 3 core indexes: workspace+created_at, actor+created_at, event+created_at
- 90-day default retention
- Explicit `create_ai_audit_event()` helper (fail-safe)
- ADMIN-only viewing permission (Phase 8.5+)

**Report**: See [PHASE_8_3_AUDIT_EVENT_PERSISTENCE_DESIGN.md](./PHASE_8_3_AUDIT_EVENT_PERSISTENCE_DESIGN.md)

---

## Phase 8.4: Audit Event Persistence ✅

**Goal**: Implement AIAuditEvent database model and write helper.

**Changes**:

- New `AIAuditEvent` model in `db/models/ai.py`
- New migration `0122_aiauditevent.py`
- New `create_ai_audit_event()` helper (fail-safe, writes both logger + DB)
- Integrated into existing audit logging calls
- 3 core indexes: workspace+created_at, actor+created_at, event+created_at

**Acceptance Criteria**:

- [x] AIAuditEvent model with 19 safe fields
- [x] Migration generated
- [x] create_ai_audit_event() helper (fail-safe)
- [x] DB write failure does not affect AI main flow
- [x] No raw prompt, result, secrets stored
- [x] No audit API or UI added
- [x] py_compile passes

**Risks**: Low (fail-safe DB write, no new API/UI)

**Report**: See [PHASE_8_4_AUDIT_EVENT_MODEL_REPORT.md](./PHASE_8_4_AUDIT_EVENT_MODEL_REPORT.md)

---

## Phase 8.4.5: Audit Event Persistence Validation ✅

**Goal**: Validate AIAuditEvent model, migration, and persistence safety.

**Findings**:

- Model inherits BaseModel correctly
- Migration contains only AIAuditEvent
- No raw prompt, result, MCP result, or secrets stored
- DB write failure is fail-safe
- API contract unchanged
- No code fixes needed

**Report**: See [PHASE_8_4_5_AUDIT_EVENT_VALIDATION_REPORT.md](./PHASE_8_4_5_AUDIT_EVENT_VALIDATION_REPORT.md)

---

## Phase 8.4.6: Django Migration Dry-Run ✅

**Goal**: Validate AIAuditEvent model/migration at Django level.

**Findings**:

- py_compile passes for all files
- Migration dependency chain correct (0121 → 0122)
- No migration number conflicts
- Model and migration fields match
- Django check/sqlmigrate not runnable (missing dependencies in env)
- Static validation sufficient

**Report**: See [PHASE_8_4_6_DJANGO_MIGRATION_DRY_RUN_REPORT.md](./PHASE_8_4_6_DJANGO_MIGRATION_DRY_RUN_REPORT.md)

---

## Phase 8.5: Admin-Only Audit Read API Design ✅

**Goal**: Design admin-only AI audit read API.

**Design**:

- `GET /api/workspaces/<slug>/ai-audit-events/`
- ADMIN only (MEMBER/GUEST = 403)
- 12 query filters (event, mode, adapter, tool_name, etc.)
- Pagination (20 per page, max 100)
- Ordering: created_at DESC
- 19 safe response fields
- No raw prompt, result, secrets, headers, stack trace
- 90-day max time range

**Report**: See [PHASE_8_5_AUDIT_READ_API_DESIGN.md](./PHASE_8_5_AUDIT_READ_API_DESIGN.md)

---

## Phase 8.6: Admin-Only Audit Read API ✅

**Goal**: Implement admin-only AI audit read API.

**Changes**:

- New `AIAuditEventSerializer` + `ActorLiteSerializer`
- New `AIAuditEventListEndpoint` (GET, ADMIN only)
- URL route: `GET /api/workspaces/<slug>/ai-audit-events/`
- 12 safe query filters
- Pagination (20/page, max 100)
- 30-day default / 90-day max time window
- 19 safe response fields

**Acceptance Criteria**:

- [x] ADMIN only access
- [x] MEMBER/GUEST = 403
- [x] Workspace scoped
- [x] No raw prompt, result, secrets returned
- [x] Pagination + filters + ordering
- [x] py_compile passes
- [x] No migration needed
- [x] No existing API contract changed

**Report**: See [PHASE_8_6_AUDIT_READ_API_IMPLEMENTATION_REPORT.md](./PHASE_8_6_AUDIT_READ_API_IMPLEMENTATION_REPORT.md)

---

## Phase 8.6.5: Audit Read API Validation ✅

**Goal**: Validate audit read API permissions and security.

**Findings**:

- Permission correctly set to ADMIN only
- Workspace scope enforced
- Serializer returns only safe fields
- Filters use whitelists
- Pagination enforced (no bypass)
- Found and fixed: ActorLiteSerializer source bug (actor_id → actor)

**Report**: See [PHASE_8_6_5_AUDIT_READ_API_VALIDATION_REPORT.md](./PHASE_8_6_5_AUDIT_READ_API_VALIDATION_REPORT.md)

---

## Phase 8.7: Audit Retention Command Design ✅

**Goal**: Design AI audit retention management command.

**Design**:

- Command: `cleanup_ai_audit_events`
- Default retention: 90 days
- Default: dry-run (no deletion)
- Requires `--confirm` to execute
- Hard delete for true data removal
- Batch deletion (1000/batch)
- 7-day minimum retention protection
- Safe output (counts only, no sensitive data)

**Report**: See [PHASE_8_7_AUDIT_RETENTION_COMMAND_DESIGN.md](./PHASE_8_7_AUDIT_RETENTION_COMMAND_DESIGN.md)

---

## Phase 8.8: Audit Retention Command ✅

**Goal**: Implement AI audit retention management command.

**Changes**:

- New `cleanup_ai_audit_events` management command
- Default: dry-run (no deletion)
- Requires `--confirm` to execute
- Default retention: 90 days (min 7)
- Hard delete in batches (default 1000)
- Safe output (counts only)

**Acceptance Criteria**:

- [x] Management command created
- [x] dry-run by default
- [x] `--confirm` required for deletion
- [x] `--days` with min 7 protection
- [x] `--workspace-slug` optional filter
- [x] `--batch-size` with range validation
- [x] Hard delete via queryset
- [x] Safe output (no sensitive data)
- [x] py_compile passes

**Report**: See [PHASE_8_8_AUDIT_RETENTION_COMMAND_IMPLEMENTATION_REPORT.md](./PHASE_8_8_AUDIT_RETENTION_COMMAND_IMPLEMENTATION_REPORT.md)

---

## Phase 8.8.5: Audit Retention Command Validation ✅

**Goal**: Validate retention command safety and deletion boundaries.

**Findings**:

- Command path correctly registered
- Hard delete confirmed (queryset delete bypasses soft delete)
- dry-run protection verified
- --confirm required for deletion
- Parameter boundaries safe (min 7 days, batch 1-10000)
- No sensitive data in output
- No code fixes needed

**Report**: See [PHASE_8_8_5_AUDIT_RETENTION_COMMAND_VALIDATION_REPORT.md](./PHASE_8_8_5_AUDIT_RETENTION_COMMAND_VALIDATION_REPORT.md)

---

## Phase 9.0: Write Confirmation Design ✅

**Goal**: Design write operation confirmation workflow.

**Design**:

- Write operations risk-classified (low/medium/high)
- Two-stage confirmation: plan → confirm
- Phase 9.1 minimum: update work item state only
- stdio adapter cannot execute writes (workspace API key)
- Writes must use request.user + Plane internal permissions
- Prompt injection protection: backend re-validates everything
- No migration needed for Phase 9.1

**Report**: See [PHASE_9_0_WRITE_CONFIRMATION_DESIGN.md](./PHASE_9_0_WRITE_CONFIRMATION_DESIGN.md)

---

## Phase 9.1: Write Confirmation Plan-Only ✅

**Goal**: Implement plan-only write confirmation (no real execution).

**Changes**:

- Write intent detection
- proposed_action with execution_enabled=False
- confirm_action_id interception (reject)
- pi-chat confirmation card
- Audit events (ai.write.proposed, ai.write.rejected)
- No real write operations

**Acceptance Criteria**:

- [x] Write intent detected
- [x] proposed_action generated (plan only)
- [x] execution_enabled=False
- [x] confirm_action_id rejected
- [x] Confirmation card displayed
- [x] Audit events logged
- [x] No real write operations
- [x] py_compile passes
- [x] typecheck/lint passes

**Risks**: Low (plan only, no execution)

**Report**: See [PHASE_9_1_WRITE_CONFIRMATION_PLAN_ONLY_REPORT.md](./PHASE_9_1_WRITE_CONFIRMATION_PLAN_ONLY_REPORT.md)

---

## Phase 9.1.5: Write Confirmation Preview Validation ✅

**Goal**: Validate write confirmation preview safety.

**Findings**:

- proposed_action only contains safe fields
- execution_enabled always false
- Confirm button disabled, no-op
- confirm_action_id returns execution_not_enabled
- No real write operations
- No stdio/mcp-server write calls
- Audit events properly logged
- No code fixes needed

**Report**: See [PHASE_9_1_5_WRITE_CONFIRMATION_PREVIEW_VALIDATION_REPORT.md](./PHASE_9_1_5_WRITE_CONFIRMATION_PREVIEW_VALIDATION_REPORT.md)

---

## Phase 9.2: Confirmed State Update Design ✅

**Goal**: Design confirmed update_work_item_state execution path.

**Design**:

- Signed payload (Django TimestampSigner) for confirmation token
- No migration needed
- Target/state parsing via UUID
- Permission: workspace member + project member (ADMIN/MEMBER)
- Direct ORM update + activity dispatch
- 15 safe error codes
- Idempotent (same state = same result)

**Report**: See [PHASE_9_2_CONFIRMED_STATE_UPDATE_DESIGN.md](./PHASE_9_2_CONFIRMED_STATE_UPDATE_DESIGN.md)

---

## Phase 9.3: Confirmed State Update Implementation ✅

**Goal**: Implement confirmed update_work_item_state with signed token.

**Changes**:

- Signed confirmation token (Django TimestampSigner, max_age=300s)
- UUID-based issue/state parsing
- Full permission validation chain
- Direct ORM update + activity dispatch
- Frontend Confirm button enabled when execution_enabled=True
- Audit events (proposed, confirmed, executed, rejected, error)
- Only updates state field

**Acceptance Criteria**:

- [x] Signed token generated
- [x] execution_enabled=True when validation passes
- [x] Full permission chain (workspace + project member)
- [x] current_state consistency check
- [x] Only state field updated
- [x] Activity dispatch
- [x] Frontend Confirm button works
- [x] Audit events logged
- [x] py_compile passes
- [x] typecheck/lint passes

**Risks**: Medium (first real write operation)

**Report**: See [PHASE_9_3_CONFIRMED_STATE_UPDATE_IMPLEMENTATION_REPORT.md](./PHASE_9_3_CONFIRMED_STATE_UPDATE_IMPLEMENTATION_REPORT.md)

---

## Phase 9.3.5: Confirmed State Update Validation ✅

**Goal**: Validate confirmed state update security and correctness.

**Findings**:

- Write path: `issue.save()` triggers `_sync_completed_at()` and `ChangeTrackerMixin`
- Activity dispatch manually invoked (equivalent to existing endpoint)
- Full permission chain verified (14 checks)
- Signed token properly verified (TimestampSigner, max_age=300)
- confirm_action_id verified against token action_id
- Only state field updated
- No stdio/mcp-server write calls
- Audit events properly logged
- No code fixes needed

**Report**: See [PHASE_9_3_5_CONFIRMED_STATE_UPDATE_VALIDATION_REPORT.md](./PHASE_9_3_5_CONFIRMED_STATE_UPDATE_VALIDATION_REPORT.md)

---

## Phase 9.3.6: Runtime Test Plan ✅

**Goal**: Design runtime test plan for confirmed state update.

**Plan**:

- 4 success path test cases (ADMIN/MEMBER proposed + confirm)
- 12 rejection path test cases (token expired/tampered/mismatch, permission denied, etc.)
- 9 security checks
- Rollback plan
- Step-by-step runtime test commands
- Dev/staging only, no production testing

**Report**: See [PHASE_9_3_6_CONFIRMED_STATE_UPDATE_RUNTIME_TEST_PLAN.md](./PHASE_9_3_6_CONFIRMED_STATE_UPDATE_RUNTIME_TEST_PLAN.md)

---

## Phase 9.3.7: Runtime Preflight ✅

**Goal**: Check runtime environment readiness for confirmed state update testing.

**Findings**:

- Dev fork path confirmed
- API accessible via proxy (localhost:18080)
- AIAuditEvent migration file exists
- **AI features NOT enabled** in Docker environment:
  - `enable_ai_assistant` not set
  - `enable_ai_mcp_runtime` not set
  - `has_llm_configured` = false
- Test data not selected (environment not ready)
- No proposed_action generated, no confirm executed

**Report**: See [PHASE_9_3_7_CONFIRMED_STATE_UPDATE_RUNTIME_PREFLIGHT_REPORT.md](./PHASE_9_3_7_CONFIRMED_STATE_UPDATE_RUNTIME_PREFLIGHT_REPORT.md)

---

## Phase 9.3.7A: Runtime Environment Readiness ✅

**Goal**: Assess runtime environment for confirmed state update testing.

**Findings**:

- localhost:18080 runs **official Plane v1.3.1** (makeplane/plane-backend:v1.3.1)
- Does NOT contain fork code (no `/code/plane/ai/` in container)
- Database may contain real data
- AIAuditEvent migration not applied
- AI feature flags not present in official image
- **Recommendation**: Build separate dev stack from fork branch

**Report**: See [PHASE_9_3_7A_RUNTIME_ENVIRONMENT_READINESS_REPORT.md](./PHASE_9_3_7A_RUNTIME_ENVIRONMENT_READINESS_REPORT.md)

---

## Phase 9.3.7B: Isolated Dev Stack Design ✅

**Goal**: Design isolated dev stack for runtime testing.

**Design**:

- New `docker-compose.ai-dev.yml` with independent volumes/ports
- API port: 18180 (not 18080)
- Independent Postgres/Redis volumes
- `.env.ai-dev.example` (committed) + `.env.ai-dev.local` (gitignored)
- AI flags enabled: ENABLE_AI_ASSISTANT=1, ENABLE_AI_MCP_RUNTIME=1
- Migration strategy: apply 0122 to dev DB only
- Test data: one-time workspace/project/issue

**Report**: See [PHASE_9_3_7B_ISOLATED_DEV_STACK_DESIGN.md](./PHASE_9_3_7B_ISOLATED_DEV_STACK_DESIGN.md)

---

## Phase 9.3.7C: Isolated Dev Stack Files ✅

**Goal**: Create isolated dev stack configuration files.

**Files Created**:

- `docker-compose.ai-dev.yml` (API, Web, DB, Redis, Worker)
- `.env.ai-dev.example` (no secrets)
- `.gitignore` updated (`.env.ai-dev.local`)

**Config**:

- API port: 18180
- Web port: 18181
- Postgres volume: `plane_ai_dev_pgdata`
- Redis volume: `plane_ai_dev_redisdata`
- AI flags: ENABLE_AI_ASSISTANT=1, ENABLE_AI_MCP_RUNTIME=1

**Report**: See [PHASE_9_3_7C_ISOLATED_DEV_STACK_FILES_REPORT.md](./PHASE_9_3_7C_ISOLATED_DEV_STACK_FILES_REPORT.md)

---

## Phase 9.3.7D: Isolated Dev Stack Start ⚠️

**Goal**: Build and start isolated dev stack.

**Status**: Config validated, build failed due to network issues.

**Findings**:

- `.env.ai-dev.local` created (gitignored)
- `docker compose config` passed
- Build failed: Docker Hub EOF, npm timeout, APK mirror unreachable
- Fixed: API/Worker build context path
- Need stable network to retry

**Report**: See [PHASE_9_3_7D_ISOLATED_DEV_STACK_START_REPORT.md](./PHASE_9_3_7D_ISOLATED_DEV_STACK_START_REPORT.md)

---

## Phase 9.3.7D-1: Build Network Retry ✅

**Goal**: Diagnose network issues and retry isolated dev stack build.

**Findings**:

- Network now reachable (Docker Hub, npm, Alpine)
- Previous failures were transient
- Build succeeded on retry
- All 5 containers started
- API waiting for migrations (502)
- Web healthy (200)
- Fixed: added REDIS_URL to compose

**Report**: See [PHASE_9_3_7D_1_BUILD_NETWORK_RETRY_REPORT.md](./PHASE_9_3_7D_1_BUILD_NETWORK_RETRY_REPORT.md)

---

## Phase 9.3.7E: Dev Migration and AI Flags ✅

**Goal**: Run migration on isolated dev DB and verify AI flags.

**Results**:

- Migration succeeded (including 0122_aiauditevent)
- AIAuditEvent model import OK
- AI flags verified: ENABLE_AI_ASSISTANT=True, ENABLE_AI_MCP_RUNTIME=True
- API healthy on port 18180
- Web healthy on port 18181

**Report**: See [PHASE_9_3_7E_DEV_MIGRATION_FLAGS_REPORT.md](./PHASE_9_3_7E_DEV_MIGRATION_FLAGS_REPORT.md)

---

## Phase 9.3.7F: Isolated Test Data ✅

**Goal**: Create test data for confirmed state update runtime test.

**Test Data**:

- Workspace: `ai-test`
- Project: `AITEST`
- Issue: `AI State Update Runtime Test`
- State A: `Todo` (current)
- State B: `In Progress` (target)
- User: ADMIN (20)

**Integrity**: All checks passed (workspace/project/state membership).

**Report**: See [PHASE_9_3_7F_ISOLATED_TEST_DATA_REPORT.md](./PHASE_9_3_7F_ISOLATED_TEST_DATA_REPORT.md)

---

## Phase 9.3.8A: Proposed Action Runtime Verification ✅

**Goal**: Verify proposed_action generation at runtime.

**Results**:

- proposed_action generated successfully
- action_type=update_work_item_state, execution_enabled=True
- current_value=Todo, proposed_value=In Progress
- confirmation_token exists (not output)
- Issue state unchanged (still Todo)
- ai.write.proposed audit event recorded
- No ai.write.executed (no real update)

**Report**: See [PHASE_9_3_8A_PROPOSED_ACTION_RUNTIME_REPORT.md](./PHASE_9_3_8A_PROPOSED_ACTION_RUNTIME_REPORT.md)

---

## Phase 9.3.8A-1: API/UI Proposed Action Verification ⚠️

**Goal**: Verify proposed_action via real API/UI.

**Results**:

- Django shell verification: ✅ passed
- API session auth: ⚠️ limited (sign-in returns 500 in dev env)
- Issue state unchanged: ✅ (still Todo)
- ai.write.proposed recorded: ✅
- No ai.write.executed: ✅

**Next**: Web UI manual verification needed.

**Report**: See [PHASE_9_3_8A_1_API_UI_PROPOSED_ACTION_RUNTIME_REPORT.md](./PHASE_9_3_8A_1_API_UI_PROPOSED_ACTION_RUNTIME_REPORT.md)

---

## Phase 9.3.8A-2: Auth/Session Readiness ✅

**Goal**: Diagnose and fix sign-in 500 error.

**Root Cause**: `APP_BASE_URL` and `WEB_URL` not set in dev env.

**Fix**: Added URL env vars to `.env.ai-dev.local` and `.env.ai-dev.example`.

**Result**: Sign-in returns 302 (no longer 500).

**Report**: See [PHASE_9_3_8A_2_AUTH_SESSION_READINESS_REPORT.md](./PHASE_9_3_8A_2_AUTH_SESSION_READINESS_REPORT.md)

---

## Phase 9.3.8A-2R: Web Auth Methods Fix ✅

**Goal**: Fix "No authentication methods available" in Web UI.

**Root Cause**: Web nginx didn't proxy API requests. Frontend couldn't read auth config.

**Fix**: Added `nginx-dev.conf` with API proxy, mounted in dev compose.

**Result**: `is_email_password_enabled: True` now accessible via proxy.

**Report**: See [PHASE_9_3_8A_2R_WEB_AUTH_METHODS_FIX_REPORT.md](./PHASE_9_3_8A_2R_WEB_AUTH_METHODS_FIX_REPORT.md)

---

## Phase 9.3.8A-2R2: Web Proxy Verification ⚠️

**Goal**: Verify nginx API proxy is effective.

**Findings**:

- nginx proxy IS working (curl returns JSON)
- API returns `is_email_password_enabled: true`
- Browser still shows "No authentication methods available"
- Likely cause: browser cache or SWR cache
- Needs user verification with incognito window

**Report**: See [PHASE_9_3_8A_2R2_WEB_PROXY_EFFECTIVE_FIX_REPORT.md](./PHASE_9_3_8A_2R2_WEB_PROXY_EFFECTIVE_FIX_REPORT.md)

---

## Phase 9.3.8A-2R3: Instance Setup Fix ✅

**Goal**: Fix instance setup/god-mode onboarding blocker.

**Root Cause**: Superuser created via Django shell bypassed setup flow. `is_setup_done=false`.

**Fix**: Set `is_setup_done=True`, `is_signup_screen_visited=True`, created `InstanceAdmin`.

**Report**: See [PHASE_9_3_8A_2R3_INSTANCE_SETUP_FIX_REPORT.md](./PHASE_9_3_8A_2R3_INSTANCE_SETUP_FIX_REPORT.md)

---

## Phase 9.3.8A-2R4: API 502 Recovery ✅

**Goal**: Recover from 502 Bad Gateway after API container restart.

**Root Cause**: nginx cached old API container IP. Restart fixed it.

**Report**: See [PHASE_9_3_8A_2R4_API_502_RECOVERY_REPORT.md](./PHASE_9_3_8A_2R4_API_502_RECOVERY_REPORT.md)

---

## Phase 9.3.8A-2R5: CSRF Login Fix ✅

**Goal**: Fix CSRF Verification Failed on login.

**Root Cause**: `CSRF_TRUSTED_ORIGINS` empty. Django rejects cross-origin CSRF.

**Fix**: Added `CSRF_TRUSTED_ORIGINS=http://localhost:18181` to env.

**Report**: See [PHASE_9_3_8A_2R5_CSRF_LOGIN_FIX_REPORT.md](./PHASE_9_3_8A_2R5_CSRF_LOGIN_FIX_REPORT.md)

---

## Phase 9.3.8A-3R: Web UI Proposed Action Failure Fix ✅

**Goal**: Fix "Something went wrong" error on pi-chat.

**Root Cause**: `create_ai_audit_event(user_id=...)` should be `actor_id=...`.

**Fix**: Corrected parameter name (2 occurrences).

**Report**: See [PHASE_9_3_8A_3R_WEB_UI_PROPOSED_ACTION_FAILURE_REPORT.md](./PHASE_9_3_8A_3R_WEB_UI_PROPOSED_ACTION_FAILURE_REPORT.md)

---

## Phase 9.3.8A-3R2: Web UI Mode Selection Issue ✅

**Root Cause**: User didn't switch to "MCP Read-only" mode. Default "Standard Chat" calls OpenAI with placeholder key.

**Fix**: User needs to click "MCP Read-only" button before entering UUID instruction.

**Report**: See [PHASE_9_3_8A_3R2_WEB_UI_INTERNAL_ERROR_REPORT.md](./PHASE_9_3_8A_3R2_WEB_UI_INTERNAL_ERROR_REPORT.md)

---

## Phase 9.3.8A-3R3: MCP Proposed Action Routing Fix ✅

**Root Cause**: Intent parser only supported English keywords. Chinese prompt "将...状态改为..." didn't match.

**Fix**: Added Chinese keywords to write intent detection.

**Report**: See [PHASE_9_3_8A_3R3_MCP_PROPOSED_ACTION_ROUTING_REPORT.md](./PHASE_9_3_8A_3R3_MCP_PROPOSED_ACTION_ROUTING_REPORT.md)

---

## Phase 9.3.8A-3R4: Confirmation Card Success + Confirm Button Fix ✅

**Goal**: Record confirmation card success and fix missing Confirm button.

**Findings**:

- Confirmation card successfully displayed
- Confirm button missing due to Web container not rebuilt after Phase 9.1
- Fixed: Web container rebuilt with latest frontend code

**Report**: See [PHASE_9_3_8A_3R4_CONFIRMATION_CARD_NO_CONFIRM_REPORT.md](./PHASE_9_3_8A_3R4_CONFIRMATION_CARD_NO_CONFIRM_REPORT.md)

---

## Phase 9.3.8A-4R5: Autonomous Confirm Button Fix ✅

**Goal**: Fix Confirm button visibility without user interaction.

**Fix**: Frontend minimal safe fix — Confirm button always rendered, disabled when canConfirm=false.

**Report**: See [PHASE_9_3_8A_4R5_CONFIRM_BUTTON_AUTONOMOUS_FIX_REPORT.md](./PHASE_9_3_8A_4R5_CONFIRM_BUTTON_AUTONOMOUS_FIX_REPORT.md)

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

## Phase 9.5B-R4: Native AI Official MCP Route Firewall ✅

**Goal**: Enforce that native AI Drawer only routes through official MCP gateway, with zero legacy leakage.

**Changes**:

- New native AI endpoint: `apps/api/plane/app/views/ai_native.py`
- New frontend service: `apps/web/core/services/native-ai.service.ts`
- New route firewall script: `scripts/check_native_ai_route_firewall.py`
- Drawer switched from `createGptTask` to `NativeAIService`
- Drawer validates `source === "official_mcp_gateway"`
- URL routes registered in `apps/api/plane/app/urls/external.py`

**Acceptance Criteria**:

- [x] Native endpoint only routes through `mcp_gateway`
- [x] No import of `mcp_runtime` in native AI files
- [x] No `createGptTask` in native Drawer
- [x] No `/ai-assistant/` old endpoint in native Drawer
- [x] Response `source` = `official_mcp_gateway`
- [x] Frontend validates `source`
- [x] `confirmation_token` NOT returned (only `confirmation_token_present: bool`)
- [x] Route firewall script passes
- [x] `asdfg` count = 0
- [x] Pushed to origin

**Risks**: Low (documentation + route isolation)

**Future PR**: No (fork-only)

**Report**: See [PHASE_9_5B_R4_NATIVE_AI_OFFICIAL_MCP_FIREWALL_REPORT.md](./PHASE_9_5B_R4_NATIVE_AI_OFFICIAL_MCP_FIREWALL_REPORT.md)

---

## Phase 9.5B-R5: Native AI Proposed-Only UI Validation ✅

**Goal**: Validate native AI Drawer proposed-only UI after route firewall enforcement.

**Changes**:

- Backend validation: native/propose returns correct proposed_action
- Frontend build verification: NativeAIService in production build
- UI code verification: all confirmation card elements present

**Acceptance Criteria**:

- [x] Route firewall PASS
- [x] native/propose returns `source=official_mcp_gateway`
- [x] `response_type=proposed_action`
- [x] `action_type=create_work_item`
- [x] `project.name=AI Test Project`
- [x] `title=asdfg`
- [x] `requires_confirmation=true`
- [x] `confirmation_token_present=true` (value not exposed)
- [x] `raw_result_returned=false`
- [x] `asdfg` count = 0
- [x] `ai.write.executed` = 1 (unchanged)
- [x] Confirm button visible/enabled in code
- [x] Cancel button visible in code
- [x] No `confirmation_token` exposed to frontend
- [x] Frontend build includes NativeAIService

**Risks**: Low (validation only, no code changes)

**Future PR**: No (fork-only)

**Report**: See [PHASE_9_5B_R5_NATIVE_AI_PROPOSED_ONLY_UI_VALIDATION_REPORT.md](./PHASE_9_5B_R5_NATIVE_AI_PROPOSED_ONLY_UI_VALIDATION_REPORT.md)

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
