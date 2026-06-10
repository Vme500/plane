# ECC Project Configuration — Plane AI

## Project Overview

This is the Plane AI fork for implementing MCP-based AI assistant features.

## AI Architecture

- **Official plane-mcp-server** is the main tools route
- **Legacy pi-ai** code remains but is not the primary execution path
- **Native AI button + Drawer** is the product UI target
- **pi-chat** is legacy/dev-only, not the primary product route

## Target Architecture

```
User → Plane AI UI → Plane AI Gateway API → LLM tool-calling → official plane-mcp-server → Plane API → confirmation / audit / sanitized response
```

## Dev Environment

- API: `http://localhost:18180`
- Web: `http://localhost:18181`
- compose project: `plane-ai-dev`
- compose file: `docker-compose.ai-dev.yml`

## Recommended Agents

- planner — implementation planning
- architect — system design
- code-reviewer — code quality review
- security-reviewer — security analysis
- typescript-reviewer — TypeScript/React review
- python-reviewer — Python/Django review
- database-reviewer — database review
- build-error-resolver — build error resolution
- doc-updater — documentation sync

## Recommended Skills

- coding-standards
- backend-patterns
- frontend-patterns
- django-patterns
- django-security
- django-tdd
- python-patterns
- python-testing
- security-review
- tdd-workflow
- verification-loop

## Standing Rules

- CLAUDE.md project rules take priority over ECC generic suggestions
- After phase completion, auto-commit and push to origin current branch
- Do not create PR unless explicitly asked
- Do not modify 18080 production environment
- Do not output secrets, tokens, or passwords
