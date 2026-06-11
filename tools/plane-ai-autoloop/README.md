# Plane AI AutoLoop Harness

## Purpose

Controlled autonomous development loop for Plane AI native MCP assistant. Claude Code runs checks, fixes, and validations automatically — but stops at user gates.

## Boundaries

- **Can**: check status, fix dev-only code, commit, push, run tests, create docs
- **Cannot**: click Confirm, create asdfg, execute real writes, affect 18080
- **Must stop at**: user login, manual screenshot, Confirm approval

## User Gates

| Gate                     | Description                                    |
| ------------------------ | ---------------------------------------------- |
| First-time browser login | User must login in dedicated Edge Profile once |
| Manual screenshot        | If CDP unavailable, user takes screenshot      |
| Confirm click            | Only in 9.5C with explicit user approval       |

## How to Run

```bash
bash tools/plane-ai-autoloop/run_checks.sh
```

## JSON Report

Each round outputs a compact JSON report matching `round_report_template.json`.

Status values:

- `continue` — auto loop can proceed
- `completed` — phase done
- `blocked` — technical blocker
- `needs_user_action` — user must act before continuing

## Forbidden

- No `/ai-test/pi-chat` as primary entry
- No legacy `mcp_runtime` expansion
- No `createGptTask` in native route
- No `confirmation_token` output
- No `.env.ai-dev.local` commits
- No Edge Profile commits
- No PR creation
