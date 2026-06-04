# 第 9.3.8F 阶段报告：PR Packaging and Clean-Branch Strategy Review

> 日期：2026-06-03
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：分析完成，建议创建 clean PR branch

---

## 1. Commit 范围

| 项目                  | 值         |
| --------------------- | ---------- |
| 相对 upstream/preview | 71 commits |
| 变更文件数            | 184        |
| 插入行数              | 22,712     |
| 删除行数              | 4,023      |

---

## 2. 变更文件分类

| 类别           | 文件数 | 说明                               |
| -------------- | ------ | ---------------------------------- |
| 代码文件       | 102    | MCP runtime, model, endpoint, UI   |
| 文档文件       | 78     | 30+ phase reports                  |
| Dev stack 文件 | 3      | docker-compose, nginx, env example |
| 其他           | 1      | pnpm-lock, workspace config        |

---

## 3. 当前分支是否适合直接 PR

**不建议直接 PR。**

原因：

1. **71 commits** 太多，需要压缩
2. **78 个文档文件** 大部分是内部阶段报告，不适合 upstream
3. **pnpm-lock.yaml** 有大量无关变更
4. **缺少正式 tests**
5. **inline styles** 需要整理

---

## 4. 建议：创建 clean PR branch

**推荐方案 B：创建 clean PR branch。**

### Clean branch 名称

`feat/ai-mcp-confirmed-write-clean`

### Base 分支

`upstream/preview`

### Cherry-pick 策略

**必须包含的代码文件：**

| 文件                                                               | 说明                                     |
| ------------------------------------------------------------------ | ---------------------------------------- |
| `apps/api/plane/ai/mcp_runtime.py`                                 | MCP runtime + proposed_action + dispatch |
| `apps/api/plane/ai/mcp_tools.py`                                   | Read-only tool whitelist + mock adapter  |
| `apps/api/plane/ai/mcp_stdio_adapter.py`                           | stdio adapter prototype                  |
| `apps/api/plane/ai/audit_logger.py`                                | Safe audit logger + DB helper            |
| `apps/api/plane/db/models/ai.py`                                   | AIAuditEvent model                       |
| `apps/api/plane/db/models/__init__.py`                             | Model registration                       |
| `apps/api/plane/db/migrations/0122_aiauditevent.py`                | Migration                                |
| `apps/api/plane/db/management/commands/cleanup_ai_audit_events.py` | Retention command                        |
| `apps/api/plane/app/views/ai.py`                                   | Admin audit read API                     |
| `apps/api/plane/app/views/external/base.py`                        | Endpoint (MCP mode + confirm)            |
| `apps/api/plane/app/serializers/ai.py`                             | Audit serializer                         |
| `apps/api/plane/app/urls/external.py`                              | URL route                                |
| `apps/web/app/.../pi-chat/page.tsx`                                | MCP Preview + confirmation card          |

**必须包含的 dev stack 文件：**

| 文件                            | 说明               |
| ------------------------------- | ------------------ |
| `docker-compose.ai-dev.yml`     | Isolated dev stack |
| `.env.ai-dev.example`           | Env template       |
| `apps/web/nginx/nginx-dev.conf` | Dev nginx config   |
| `.gitignore`                    | Updated            |

**必须包含的精简文档：**

| 文件                                                 | 说明                   |
| ---------------------------------------------------- | ---------------------- |
| `docs/ai-assistant/AI_ROADMAP.md`                    | Concise roadmap        |
| `docs/ai-assistant/PHASE_2_ARCHITECTURE_DECISION.md` | Architecture decisions |

**不应进入 PR 的内部材料（30+ 文件）：**

- 所有 `PHASE_*_REPORT.md` 文件
- 所有 `PHASE_*_VALIDATION_REPORT.md` 文件
- 所有 `PHASE_*_DIAGNOSIS_REPORT.md` 文件
- 所有 `PHASE_*_FIX_REPORT.md` 文件
- `PHASE_9_3_8*_REPORT.md` 文件
- 本地调试记录
- Windows/WSL/Edge 自动化失败记录

---

## 5. 建议 Commit 组织

| Commit | 内容                                                                                                                                |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| 1      | `feat: add AI MCP runtime and audit model` — mcp_runtime, mcp_tools, mcp_stdio_adapter, audit_logger, AIAuditEvent model, migration |
| 2      | `feat: add AI assistant endpoint and confirmed write flow` — base.py endpoint, ai.py serializer/view/urls, retention command        |
| 3      | `feat: add MCP preview and confirmation card UI` — pi-chat page.tsx                                                                 |
| 4      | `chore: add isolated AI dev stack` — docker-compose, nginx, env example, gitignore                                                  |
| 5      | `docs: add AI assistant architecture and roadmap` — concise docs                                                                    |

---

## 6. 非阻塞风险

| 风险                 | 说明                                |
| -------------------- | ----------------------------------- |
| mock adapter 命名    | 可改为 `direct-db` 或 `dev-adapter` |
| Inline styles        | 后续整理为组件样式                  |
| 无 automated tests   | 后续补充                            |
| 无 rollback strategy | 后续新建测试 issue                  |

---

## 7. 建议 PR 标题

```
feat: add AI MCP preview and confirmed work item state updates
```

---

## 8. 建议 PR Body

```
Summary:
- Add MCP-backed AI assistant runtime for work item preview
- Add safe proposed_action / confirmation flow
- Add audited confirmed update_work_item_state execution
- Add Web pi-chat MCP preview and confirmation card
- Add isolated dev stack support

Safety:
- Writes require explicit confirmation
- confirmation_token never displayed or persisted in audit
- raw_result_returned=false
- replay/expiry/current_state checks
- workspace/project/target validation
- stdio/plane-mcp-server write not enabled
- audit chain proposed → confirmed → executed

Testing:
- proposed_action generated
- Web card displayed
- Confirm button visible/enabled
- Todo → In Progress confirmed execution
- ai.write.executed=1
- no confirm_action_id / fake confirm_action_id rejected
- token/raw prompt/raw result grep clean
- 18080 unaffected

Known limitations:
- automated browser tests not yet added
- rollback strategy not included
- mock/direct adapter naming should be clarified
- inline style cleanup may be improved later
```
