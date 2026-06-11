# CLAUDE.md

## Project Standing Instructions

### 1. Current AI Architecture

- The official `plane-mcp-server` route is the main AI tools route.
- Legacy pi-ai code may remain in the repository, but it is not the primary execution path.
- Do not extend the legacy pi-ai handwritten intent parser unless explicitly requested.
- Do not expand the direct DB adapter as the product path.
- Official MCP provides Plane read/write tools and CRUD.
- Plane project code should provide UI, settings, MCP gateway, LLM tool-calling, confirmation, audit, and safety controls.

Target architecture:

```
User
→ Plane AI UI
→ Plane AI Gateway API
→ LLM tool-calling
→ official plane-mcp-server
→ Plane API
→ confirmation / audit / sanitized response
```

### 2. Local Dev Environment

Use only the isolated dev stack unless the user explicitly says otherwise:

- API: `http://localhost:18180`
- Web: `http://localhost:18181`
- compose project: `plane-ai-dev`
- compose file: `docker-compose.ai-dev.yml`
- env file: `.env.ai-dev.local`

**Never modify or rely on:**

- `18080` official/local production-like environment
- `/home/qq402/services/plane`
- Unrelated Docker compose projects

Recommended commands:

```bash
docker compose -p plane-ai-dev --env-file .env.ai-dev.local -f docker-compose.ai-dev.yml ps
docker compose -p plane-ai-dev --env-file .env.ai-dev.local -f docker-compose.ai-dev.yml build api worker web
docker compose -p plane-ai-dev --env-file .env.ai-dev.local -f docker-compose.ai-dev.yml up -d api worker web
```

### 3. Git Workflow

At the beginning of every phase:

```bash
git status --short
git branch --show-current
git log --oneline -30
git remote -v
```

Default branch: `feat/ai-phase-6-mcp-readonly-runtime`

Default push target: `origin` same branch

Default rule:

- After a phase creates a commit and checks pass, **push automatically** to `origin` current branch.
- Do not create PR unless the user explicitly asks.
- Do not push to upstream.
- Do not create upstream issues.
- Do not rebase or merge upstream unless explicitly requested.

Before push:

```bash
git ls-remote origin <current-branch>
git log --oneline origin/<current-branch>..HEAD || true
```

Push:

```bash
git push -u origin <current-branch>
```

After push:

```bash
git ls-remote origin <current-branch>
```

Push report must include:

1. Local HEAD before push
2. Remote HEAD before push
3. Whether push succeeded
4. Remote HEAD after push
5. Remote name and URL
6. Branch name
7. Whether `.env.ai-dev.local` remains untracked
8. Whether PR was created
9. Whether worktree is clean

### 4. Secret and Safety Rules

**Never output or commit:**

- API keys
- Bearer tokens
- Cookies
- Session IDs
- CSRF tokens
- Authorization headers
- Passwords
- `confirmation_token` values
- `.env.ai-dev.local`

**Allowed:**

- Field names such as `confirmation_token` or `confirm_action_id`
- Masked/configured booleans such as `secret_configured=true`

Required grep before commit:

```bash
grep -R "sk-\|api_key=.*[^=]\|password=.*[^=]\|cookie=.*[A-Za-z0-9_.-]\|Authorization\|Bearer\|session=[A-Za-z0-9_.-]\|csrf.*[A-Za-z0-9_.-]\|confirmation_token.*[A-Za-z0-9_.-]\|confirm_action_id.*[A-Za-z0-9_.-]" -ni docs/ai-assistant/ apps/web/app apps/api/plane docker-compose.ai-dev.yml .env.ai-dev.example apps/web/nginx/nginx-dev.conf || true
```

**Do not commit:**

- `.env.ai-dev.local`
- tmp scripts
- tmp clones
- browser profiles
- screenshots
- `node_modules`
- Accidental lockfile changes

### 5. Write Operation Policy

Default:

- **Do not execute real writes.**
- **Do not click Confirm.**
- **Do not create/update/delete work items/projects/states** unless the phase explicitly says confirmed write execution is allowed.

All write tools must follow:

```
natural language
→ LLM/tool selection or validated dev fallback
→ proposed_action
→ confirmation card
→ user Confirm
→ MCP write tool execution
→ audit proposed → confirmed → executed
```

All write operations require:

- Tool allowlist
- Workspace/project permission checks
- Confirmation token
- Token expiry/replay protection
- Sanitized response
- `raw_result_returned=false`

### 6. MCP Validation Rules

Do not confuse these concepts:

- **tool discovery/list_tools** only proves a tool exists
- **list_tools** does not prove `list_projects` works
- A backend `proposed_action` does not prove the Web confirmation card is visible
- Host `uvx` success does not prove Docker container runtime success
- A direct DB query does not prove official MCP route success

**A valid official MCP read test must:**

- Call through `mcp_gateway` / `official_mcp_client`
- Launch or connect official `plane-mcp-server` from API container runtime
- Call the actual tool, for example `list_projects`
- Not use direct DB
- Not use legacy pi-ai adapter
- Return sanitized result
- Not output secrets

**A valid `create_work_item` proposed-only test must prove:**

- Official MCP route is used
- `create_work_item` tool exists
- Project name resolves
- Title resolves
- `proposed_action` is generated
- Web confirmation card is visible
- Confirm is visible/enabled
- Cancel is visible
- Confirm is **not** clicked
- No work item is created
- `ai.write.proposed` increases
- `ai.write.executed` does not increase

### 6.1 Native AI Route Firewall (9.5B-R4) ✅

Native AI route is isolated from legacy. Verified by `scripts/check_native_ai_route_firewall.py`:

- `ai_native.py` only imports `mcp_gateway`, never `mcp_runtime`
- Frontend `ai-assistant-drawer.tsx` uses `NativeAIService`, not `createGptTask`
- Response `source` = `official_mcp_gateway`
- Frontend validates `source === "official_mcp_gateway"`
- `confirmation_token` NOT returned to frontend

Run `python3 scripts/check_native_ai_route_firewall.py` to re-verify.

### 7. UI Validation Rules

For Web AI tests use:

```
http://localhost:18181/ai-test/pi-chat
```

The UI should **not** show:

- "Standard Chat" when MCP Tools mode is selected
- "Read-only queries only"
- "unknown tool" for supported official MCP actions
- Raw JSON
- `confirmation_token`
- Debug rows

The UI **should** show for `create_work_item`:

- `create_work_item`
- Project: AI Test Project
- Title: asdfg
- "Confirmation required"
- Confirm button
- Cancel button

If browser automation fails, ask the user for manual screenshot verification. Do not spend excessive time fighting browser automation.

### 7.1 Dedicated Edge Profile for UI Testing

Use a dedicated Edge profile to avoid polluting the user's main browser:

```
%LOCALAPPDATA%\Microsoft\Edge\User Data\PlaneAI-MCP-Test
```

Launch with remote debugging port `9223`:

```powershell
Start-Process msedge -ArgumentList '--remote-debugging-port=9223','--user-data-dir=$env:LOCALAPPDATA\Microsoft\Edge\User Data\PlaneAI-MCP-Test','--no-first-run','--new-window','http://localhost:18181/ai-test/projects'
```

Rules:

- Never use the user's default Edge profile for testing
- Never commit cookies, sessions, or profile data
- The dedicated profile is for UI verification only
- User completes one-time login in the dedicated profile

### 8. Documentation and Phase Reports

Phase reports go under: `docs/ai-assistant/`

When a phase changes architecture or roadmap, update:

- `docs/ai-assistant/AI_ROADMAP.md`
- `docs/ai-assistant/PHASE_2_ARCHITECTURE_DECISION.md`
- The immediately previous relevant phase report

Final Chinese report should include:

- Branch
- Commit hash
- Worktree status
- Files changed
- Tests run
- Whether business data changed
- Whether 18080 was affected
- Whether secrets were output
- Whether push happened
- Whether PR was created
- Next recommended phase

### 9. Current Known Project State

Current important facts:

- Official MCP route is the main path
- Docker API dev container has uv/uvx available
- `plane-mcp-server` is available in API container
- Tool discovery found 109 tools
- `create_work_item` and `update_work_item` exist
- `list_projects` has been validated through official MCP route
- AI Test Project is visible through official MCP `list_projects`
- `create_work_item` proposed_action backend path has been validated
- Web confirmation card for official MCP `create_work_item` still needs validation/fix
- `asdfg` must not be created until an explicit confirmed create test phase

### 10. Known Current UI Issue

Current Web UI issue:

- User manually opened `http://localhost:18181/ai-test/pi-chat`
- UI still showed:
  - Mode: Standard Chat
  - Read-only queries only
  - `[MCP] unknown tool`
- This means official MCP backend `proposed_action` is not yet wired correctly to the Web UI, or the Web bundle/mode state is stale.
- Before confirmed `create_work_item` testing, fix or validate the Web confirmation card.

### 11. ECC Integration

ECC (Engineering Coding Companion) is configured as a development harness.

**Project-level rules**: `.claude/rules/ecc/` (common, typescript, python)

**Project config**: `.claude/ecc-project-config.md`

**Recommended agents**:

- planner, architect, code-reviewer, security-reviewer
- typescript-reviewer, python-reviewer, database-reviewer
- build-error-resolver, doc-updater

**Recommended skills**:

- coding-standards, backend-patterns, frontend-patterns
- django-patterns, django-security, django-tdd
- python-patterns, python-testing
- security-review, tdd-workflow, verification-loop

**Priority**: CLAUDE.md project rules take priority over ECC generic suggestions.

**Auto-push rule**: After phase completion, auto-commit and push to origin current branch per CLAUDE.md standing instructions.
