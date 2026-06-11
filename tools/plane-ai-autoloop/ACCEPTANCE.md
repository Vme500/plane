# AutoLoop Acceptance Criteria

## Global (every round)

- [ ] Route firewall PASS
- [ ] Secret scan PASS (no real secrets)
- [ ] `.env.ai-dev.local` not tracked
- [ ] 18080 unaffected
- [ ] No PR created
- [ ] No real write unless user explicitly approves
- [ ] `asdfg` count = 0 (before 9.5C)
- [ ] `ai.write.executed` = 1 (before 9.5C)

## Proposed-Only UI

- [ ] AI Assistant visible
- [ ] Drawer opens
- [ ] Provider: official MCP visible
- [ ] Write Operation Proposed visible
- [ ] Action=create_work_item visible
- [ ] Project=AI Test Project visible
- [ ] Title=asdfg visible
- [ ] Confirm visible/enabled
- [ ] Cancel visible
- [ ] No confirmation_token displayed
- [ ] No raw JSON displayed
- [ ] No Confirm click
- [ ] No asdfg creation

## User Gates

| Gate                     | When                | Action                              |
| ------------------------ | ------------------- | ----------------------------------- |
| First-time browser login | AUTO-3              | User logs in dedicated Edge Profile |
| Manual screenshot        | AUTO-3 if CDP fails | User takes screenshot               |
| Confirm click            | 9.5C only           | User explicitly approves            |
