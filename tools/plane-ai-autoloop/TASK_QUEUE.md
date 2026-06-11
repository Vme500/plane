# AutoLoop Task Queue

## AUTO-1: Create AutoLoop harness ✅

Status: Complete

## AUTO-2: Stabilize dev-only E2E identity

Status: Pending

Goal: Establish a working dev-only E2E test account for browser validation.

Checks:

- [ ] e2e_user_exists
- [ ] e2e_user_login_ready
- [ ] workspace_member
- [ ] project_permission
- [ ] mcp_workspace_slug=ai-test

## AUTO-3: Dedicated Edge Profile login and proposed-only validation

Status: Pending (blocked on AUTO-2)

Goal: Login in dedicated Edge Profile and validate proposed card end-to-end.

Checks:

- [ ] Edge Profile launched
- [ ] CDP accessible
- [ ] Login successful
- [ ] AI Assistant visible
- [ ] Drawer opens
- [ ] Proposed card renders correctly
- [ ] asdfg count=0
- [ ] ai.write.executed=1

## AUTO-4: Prepare native confirmed create test

Status: Pending (blocked on AUTO-3)

Goal: Verify confirm endpoint exists and routes through official MCP gateway. Do NOT execute.

Checks:

- [ ] Confirm endpoint exists
- [ ] Routes through mcp_gateway
- [ ] Does not import mcp_runtime
- [ ] No real execution

## AUTO-5: Post-confirm verification template

Status: Blocked until user approval of 9.5C

Goal: Template for verifying work item creation after user clicks Confirm.

User gate: Requires explicit user approval before execution.
