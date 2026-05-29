# 第 8.3 阶段报告：AIAuditEvent Database Persistence Design

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：设计完成，未写代码

---

## 1. 当前分支和 commit

| 项目        | 值                                                          |
| ----------- | ----------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                      |
| 最新 commit | `a59d52715d` — `docs: validate AI MCP audit logging safety` |
| 工作区状态  | 干净（无未提交修改）                                        |

---

## 2. 现有 Plane model/activity/logging 调研

### Base classes

| Class                           | 文件                | 说明                                                                                       |
| ------------------------------- | ------------------- | ------------------------------------------------------------------------------------------ |
| `BaseModel(AuditModel)`         | `db/models/base.py` | 所有 model 的基类，含 `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` |
| `ProjectBaseModel(BaseModel)`   | `db/models/base.py` | 添加 `project` FK + `workspace` FK                                                         |
| `WorkspaceBaseModel(BaseModel)` | `db/models/base.py` | 添加 `workspace` FK                                                                        |

### Activity models

| Model            | 继承               | 表名                | 说明                                                                   |
| ---------------- | ------------------ | ------------------- | ---------------------------------------------------------------------- |
| `IssueActivity`  | `ProjectBaseModel` | `issue_activities`  | Issue 级活动（verb, field, old/new value, actor）                      |
| `APIActivityLog` | `BaseModel`        | `api_activity_logs` | 外部 API 请求日志（token, path, method, headers, body, response_code） |

### Migration 风格

- 最新 migration：`0121_alter_estimate_type.py`
- 命名：`{NNNN}_{auto_generated_description}.py`
- 下一个应为：`0122_*`
- app label：`db`

---

## 3. AIAuditEvent schema 设计

### 推荐继承

继承 `BaseModel`（而非 `ProjectBaseModel`），因为：

- AI 请求不一定绑定 project（如 `get_me`、`list_projects`）
- workspace 通过外键关联
- `BaseModel` 提供 `created_at`, `updated_at`, `deleted_at`, `created_by`, `updated_by`

### 推荐文件位置

`apps/api/plane/db/models/ai.py`（新文件）

---

## 4. 字段表

| 字段                  | 类型                 | Nullable | Index | PII | 安全 | 说明                                                                                 |
| --------------------- | -------------------- | -------- | ----- | --- | ---- | ------------------------------------------------------------------------------------ |
| `id`                  | UUIDField            | PK       | PK    | 否  | ✅   | 自动继承 BaseModel                                                                   |
| `workspace`           | FK(Workspace)        | 否       | ✅    | 否  | ✅   | 关联 workspace                                                                       |
| `actor`               | FK(User)             | 否       | ✅    | 否  | ✅   | 操作用户                                                                             |
| `event`               | CharField(64)        | 否       | ✅    | 否  | ✅   | `ai.request`, `ai.tool.call`, `ai.tool.blocked`, `ai.tool.error`, `ai.tool.rejected` |
| `mode`                | CharField(16)        | 是       | ✅    | 否  | ✅   | `standard` / `mcp`                                                                   |
| `adapter`             | CharField(16)        | 是       | ✅    | 否  | ✅   | `none` / `mock` / `stdio`                                                            |
| `tool_name`           | CharField(64)        | 是       | ✅    | 否  | ✅   | MCP 工具名                                                                           |
| `tool_status`         | CharField(16)        | 是       | ✅    | 否  | ✅   | `success` / `blocked` / `error` / `rejected`                                         |
| `readonly`            | BooleanField         | 否       | 否    | 否  | ✅   | 始终 True                                                                            |
| `permission_filtered` | BooleanField         | 是       | 否    | 否  | ✅   | 是否经过权限过滤                                                                     |
| `raw_result_returned` | BooleanField         | 否       | 否    | 否  | ✅   | 始终 False                                                                           |
| `write_operation`     | BooleanField         | 否       | 否    | 否  | ✅   | 写操作标记（被拒绝时为 True）                                                        |
| `duration_ms`         | PositiveIntegerField | 是       | 否    | 否  | ✅   | 请求耗时（毫秒）                                                                     |
| `item_count`          | PositiveIntegerField | 是       | 否    | 否  | ✅   | 返回 item 数量                                                                       |
| `prompt_length`       | PositiveIntegerField | 是       | 否    | 否  | ✅   | prompt 字符数（非内容）                                                              |
| `error_code`          | CharField(64)        | 是       | 否    | 否  | ✅   | 安全错误码                                                                           |
| `source`              | CharField(32)        | 否       | 否    | 否  | ✅   | `pi-chat`                                                                            |
| `request_id`          | CharField(64)        | 是       | ✅    | 否  | ✅   | 请求追踪 ID                                                                          |
| `created_at`          | DateTimeField        | 自动     | ✅    | 否  | ✅   | 继承自 BaseModel                                                                     |

### 存储膨胀评估

- 每条记录约 500-800 bytes（无大文本字段）
- 1000 条/天 × 30 天 = 30,000 条 ≈ 24 MB
- 无大文本字段，存储增长可控

---

## 5. 禁止记录字段

| 字段               | 原因             |
| ------------------ | ---------------- |
| raw prompt         | 隐私             |
| raw LLM response   | 隐私             |
| raw MCP result     | 可能含敏感数据   |
| API key            | secret           |
| token              | secret           |
| cookie             | secret           |
| password           | secret           |
| request headers    | 可能含 auth 信息 |
| stack trace        | 安全             |
| env                | 安全             |
| full request body  | 安全             |
| full response body | 安全             |
| full user object   | 隐私             |
| full model object  | 安全             |
| full traceback     | 安全             |
| prompt content     | 隐私             |

---

## 6. 索引设计

### 必需索引（Phase 8.4）

| 索引              | 字段                      | 用途                      |
| ----------------- | ------------------------- | ------------------------- |
| workspace_created | `(workspace, created_at)` | 按 workspace 查询审计日志 |
| actor_created     | `(actor, created_at)`     | 按用户查询操作历史        |
| event_created     | `(event, created_at)`     | 按事件类型筛选            |

### 后置索引（Phase 8.5+）

| 索引             | 字段                       | 用途             |
| ---------------- | -------------------------- | ---------------- |
| tool_name_status | `(tool_name, tool_status)` | 工具级分析       |
| mode_adapter     | `(mode, adapter)`          | adapter 使用统计 |
| error_code       | `(error_code,)`            | 错误聚合分析     |

### 为什么不能过度索引

- 写入性能：每条 audit 记录写入时需要更新所有索引
- 存储：索引占用额外磁盘空间
- 建议先 3 个核心索引，后续按查询需求添加

---

## 7. Retention Policy

| 项目               | 建议                                                 |
| ------------------ | ---------------------------------------------------- |
| 默认保留期         | **90 天**                                            |
| 自动清理           | Phase 8.5+ 实现                                      |
| 清理方式           | Django management command（`cleanup_ai_audit_logs`） |
| 是否影响数据库大小 | 可控（无大文本字段）                                 |
| 是否需要导出       | 后置（Phase 8.6+）                                   |
| admin 可配置保留期 | 后置（Phase 8.6+）                                   |

---

## 8. 权限设计

| 阶段      | 功能                                    | 权限                                                 |
| --------- | --------------------------------------- | ---------------------------------------------------- |
| Phase 8.4 | 落库（写入）                            | endpoint 内部调用，无额外权限                        |
| Phase 8.5 | admin-only read API                     | `@allow_permission([ROLE.ADMIN], level="WORKSPACE")` |
| Phase 8.6 | Workspace Settings → AI Audit Logs 页面 | ADMIN only                                           |
| 后续      | retention 配置                          | ADMIN only                                           |

### 权限规则

- **ADMIN**：可查看所有审计日志
- **MEMBER**：不可查看
- **GUEST**：不可查看
- 不暴露 user email（只显示 user_id）
- user display name 可脱敏显示

---

## 9. 写入策略比较

### 方案 A：logger + DB handler

| 项目 | 说明                                                                         |
| ---- | ---------------------------------------------------------------------------- |
| 优点 | 复用现有 `plane.ai.audit` logger；代码改动最小                               |
| 缺点 | logging handler 异步行为不可控；难以保证写入时序；handler 异常可能影响主进程 |
| 适合 | 不推荐 Phase 8.4                                                             |

### 方案 B：显式调用 `create_ai_audit_event()`

| 项目 | 说明                                   |
| ---- | -------------------------------------- |
| 优点 | 显式控制；易于测试；fail-safe 写法明确 |
| 缺点 | 需要在调用点显式添加函数调用           |
| 适合 | ✅ **推荐 Phase 8.4**                  |

### 方案 C：先 logger，后异步落库

| 项目 | 说明                                |
| ---- | ----------------------------------- |
| 优点 | 日志和 DB 解耦；可批量写入          |
| 缺点 | 需要额外 worker；延迟写入；复杂度高 |
| 适合 | 后置（Phase 8.5+）                  |

### 推荐

**Phase 8.4 使用方案 B**：显式 `create_ai_audit_event()` helper。

```python
def create_ai_audit_event(
    workspace_slug: str,
    actor_id: str,
    event: str,
    mode: str = "standard",
    adapter: str = "none",
    tool_name: str | None = None,
    tool_status: str | None = None,
    readonly: bool = True,
    permission_filtered: bool | None = None,
    raw_result_returned: bool = False,
    write_operation: bool = False,
    duration_ms: int | None = None,
    item_count: int | None = None,
    prompt_length: int | None = None,
    error_code: str | None = None,
    source: str = "pi-chat",
    request_id: str | None = None,
) -> None:
    """Create AI audit event. Fail-safe: never raises."""
    try:
        AIAuditEvent.objects.create(...)
    except Exception:
        logger.warning("Failed to create AI audit event")
```

---

## 10. 性能与失败策略

| 项目                    | 策略                                                                 |
| ----------------------- | -------------------------------------------------------------------- |
| DB 写失败               | 不影响用户请求；记录 server logger warning                           |
| fail open / fail closed | **fail open**（审计日志失败不应阻塞 AI 功能）                        |
| duration_ms 计算        | `time.monotonic()` 计算，与现有 `now_ms()` / `duration_since()` 一致 |
| 大量 MCP list 请求      | 每次 tool call 只写一条摘要日志（item_count），不逐条记录            |
| 是否需要异步任务        | Phase 8.4 不需要（同步写一条记录，DB 写入 < 5ms）                    |
| 是否需要 batch write    | Phase 8.4 不需要                                                     |

---

## 11. 隐私与安全审查

| 要求                                 | 实现                      |
| ------------------------------------ | ------------------------- |
| 不记录 raw prompt                    | ✅ 只记录 `prompt_length` |
| 不记录 raw result                    | ✅ 只记录 `item_count`    |
| 不记录 raw MCP result                | ✅                        |
| 不记录 API key                       | ✅                        |
| 不记录 token                         | ✅                        |
| 不记录 cookie                        | ✅                        |
| 不记录 password                      | ✅                        |
| 不记录 headers                       | ✅                        |
| 不记录 stack trace                   | ✅                        |
| 不记录 env                           | ✅                        |
| 不记录 full user/model object        | ✅                        |
| error 只记录 error_code              | ✅                        |
| write operation 只记录 rejected 状态 | ✅ 不记录原始参数         |

---

## 12. 是否需要 migration

**Phase 8.3 不需要。Phase 8.4 需要。**

---

## 13. 是否需要 Docker

**否。**

---

## 14. 是否实现写操作

**否。**

---

## 15. 是否可以进入 Phase 8.4

**是。** 设计完成，可实现 AIAuditEvent model + migration + helper。

---

## 16. 是否可以进入写操作阶段

**否。** 建议先完成审计日志持久化，再考虑写操作。

---

## 17. Phase 8.4 实施记录（2026-05-28）

Phase 8.4 已按本文档设计实施，详见 [`PHASE_8_4_AUDIT_EVENT_MODEL_REPORT.md`](./PHASE_8_4_AUDIT_EVENT_MODEL_REPORT.md)。

**实施结果**：

- ✅ AIAuditEvent model 实现
- ✅ migration 生成（0122_aiauditevent.py）
- ✅ `create_ai_audit_event()` helper（fail-safe）
- ✅ 集成到现有 audit logging 调用点
