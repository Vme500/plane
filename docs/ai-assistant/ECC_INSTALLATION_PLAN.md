# ECC Installation Plan for Plane AI Project

> Date: 2026-06-03
> ECC commit: `c888d2b7` (docs: update Greptile sponsor placement)

---

## 1. ECC README Summary

ECC is a harness-native operator system for agentic work. It provides:

- 64 specialized subagents
- 261+ workflow skills
- Multi-language rules (common, typescript, python, golang, etc.)
- Hooks system
- MCP configurations
- Security scanning (AgentShield)

---

## 2. Installation Strategy

**Project-level rules** (not global):

- `.claude/rules/ecc/common/`
- `.claude/rules/ecc/typescript/`
- `.claude/rules/ecc/python/`

**Project config**: `.claude/ecc-project-config.md`

**CLAUDE.md**: Updated with ECC integration section.

---

## 3. Installed Components

| Component          | Status           | Location                             |
| ------------------ | ---------------- | ------------------------------------ |
| Rules (common)     | ✅ Installed     | `.claude/rules/ecc/common/`          |
| Rules (typescript) | ✅ Installed     | `.claude/rules/ecc/typescript/`      |
| Rules (python)     | ✅ Installed     | `.claude/rules/ecc/python/`          |
| Agents             | ⚠️ Not copied    | Use via plugin or user-level install |
| Skills             | ⚠️ Not copied    | Use via plugin or user-level install |
| Hooks              | ❌ Not installed | Plan only                            |
| MCP configs        | ❌ Not installed | Not needed (official MCP route)      |
| Plugin install     | ❌ Not done      | CLI not available                    |

---

## 4. Why Agents/Skills Not Copied

- Claude Code CLI not available in current environment
- Project-level `.claude/agents/` and `.claude/skills/` may not be stable
- Risk of context pollution with 64 agents + 261 skills
- Rules provide the most value for code quality

---

## 5. AgentShield Scan

Not run (Claude Code CLI not available). Recommended for future:

```bash
npx ecc-agentshield scan
```
