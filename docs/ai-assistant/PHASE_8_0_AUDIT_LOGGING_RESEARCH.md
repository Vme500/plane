# 第 8.0 阶段报告：AI/MCP Audit Logging Research

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：调研完成，未修改功能代码

---

## 1. 当前分支和 commit

| 项目        | 值                                                        |
| ----------- | --------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                    |
| 最新 commit | `838f621010` — `docs: validate MCP tool preview contract` |
| 工作区状态  | 干净（无未提交修改）                                      |

---

## 2. Plane 现有 audit/activity/logging 基础设施

### 2.1 Abstract Audit Mixins

| Mixin                | 文件           | 说明                                              |
| -------------------- | -------------- | ------------------------------------------------- |
| `TimeAuditModel`     | `db/mixins.py` | `created_at`, `updated_at`                        |
| `UserAuditModel`     | `db/mixins.py` | `created_by`, `updated_by`                        |
| `AuditModel`         | `db/mixins.py` | TimeAuditModel + UserAuditModel + SoftDeleteModel |
| `ChangeTrackerMixin` | `db/mixins.py` | 字段变更检测（`changed_fields`, `old_values`）    |

所有 model 通过 `BaseModel(AuditModel)` 继承审计字段。但这些是 model 级别的元数据，不是独立的审计日志表。

### 2.2 Activity Models

| Model            | 表名                | 说明                                                                  |
| ---------------- | ------------------- | --------------------------------------------------------------------- |
| `IssueActivity`  | `issue_activities`  | Issue 级活动日志（verb, field, old_value, new_value, actor）          |
| `APIActivityLog` | `api_activity_logs` | 外部 API token 请求日志（path, method, headers, body, response_code） |
| `PageLog`        | `page_logs`         | 页面实体引用跟踪（非审计日志）                                        |
| `WebhookLog`     | webhook 相关        | Webhook 投递日志                                                      |

**关键发现**：

- 没有 workspace 级别的 AuditLog model
- 没有通用的审计日志表
- `IssueActivity` 只跟踪 issue 变更
- `APIActivityLog` 记录外部 API 请求（含 headers/body，不适合 AI 场景）

### 2.3 Logging Infrastructure

| 组件                            | 文件                        | 说明                                                    |
| ------------------------------- | --------------------------- | ------------------------------------------------------- |
| `log_exception()`               | `utils/exception_logger.py` | 集中异常日志（`plane.exception` logger）                |
| `RequestLoggerMiddleware`       | `middleware/logger.py`      | 记录所有 API 请求（method, path, status, duration, IP） |
| `APITokenLogMiddleware`         | `middleware/logger.py`      | 外部 API key 请求日志（通过 Celery 写入 DB）            |
| `process_logs()`                | `bgtasks/logger_task.py`    | Celery 任务：写入 MongoDB 或 PostgreSQL                 |
| `SizedTimedRotatingFileHandler` | `utils/logging.py`          | 自定义日志文件轮转                                      |

### 2.4 Frontend

- 没有 audit log 查看页面
- `"API-enabled Audit Logs"` 在 plans.tsx 中标记为 `comingSoon: true`
- 有 issue activity UI 组件（可复用模式）

### 2.5 可复用的基础设施

| 组件                                   | 复用方式                             |
| -------------------------------------- | ------------------------------------ |
| `log_exception()`                      | AI/MCP 已在使用                      |
| `RequestLoggerMiddleware`              | 已记录 AI endpoint 的请求元数据      |
| Python `logging` 模块                  | 可用于结构化安全日志                 |
| `APIActivityLog` + `process_logs` 模式 | 可参考其 MongoDB/PostgreSQL 双写模式 |

---

## 3. 当前 AI/MCP 可审计事件

| #   | 事件                               | 来源              | 严重性 |
| --- | ---------------------------------- | ----------------- | ------ |
| 1   | standard prompt-response 请求      | endpoint          | 低     |
| 2   | mcp mode 请求                      | endpoint          | 低     |
| 3   | adapter=mock 调用                  | mcp_runtime       | 低     |
| 4   | adapter=stdio 调用                 | mcp_runtime       | 中     |
| 5   | tool success                       | mcp_runtime       | 低     |
| 6   | tool blocked（stdio 安全闸门）     | mcp_runtime       | 中     |
| 7   | tool error                         | mcp_runtime       | 中     |
| 8   | ENABLE_AI_MCP_RUNTIME=false 被拒绝 | mcp_runtime       | 低     |
| 9   | 写操作被拒绝                       | mcp_tools         | 高     |
| 10  | stdio permission gate 拒绝         | mcp_runtime       | 高     |
| 11  | stdio adapter timeout              | mcp_stdio_adapter | 中     |
| 12  | unsupported adapter                | mcp_runtime       | 低     |
| 13  | invalid mode                       | endpoint          | 低     |
| 14  | MCP server subprocess 启动失败     | mcp_stdio_adapter | 高     |

---

## 4. 推荐 audit event 字段

### 最小 schema（Phase 8.1）

| 字段                  | 类型     | 必需 | 说明                                                                                 |
| --------------------- | -------- | ---- | ------------------------------------------------------------------------------------ |
| `timestamp`           | datetime | ✅   | ISO 8601                                                                             |
| `event_type`          | string   | ✅   | `ai.request`, `ai.tool.call`, `ai.tool.blocked`, `ai.tool.error`, `ai.tool.rejected` |
| `workspace_slug`      | string   | ✅   | 当前 workspace                                                                       |
| `user_id`             | string   | ✅   | 当前 user UUID                                                                       |
| `mode`                | string   | ✅   | `standard` / `mcp`                                                                   |
| `adapter`             | string   | ✅   | `none` / `mock` / `stdio`                                                            |
| `tool_name`           | string   | 条件 | MCP 工具名                                                                           |
| `tool_status`         | string   | 条件 | `success` / `blocked` / `error` / `rejected`                                         |
| `readonly`            | boolean  | ✅   | 始终 `true`                                                                          |
| `permission_filtered` | boolean  | ✅   | 是否经过权限过滤                                                                     |
| `duration_ms`         | int      | ✅   | 请求耗时                                                                             |
| `item_count`          | int      | 条件 | 返回 item 数量                                                                       |
| `error_code`          | string   | 条件 | 错误码（非原始错误消息）                                                             |
| `source`              | string   | ✅   | `pi-chat`                                                                            |

### 可选字段

| 字段            | 类型   | 说明                  |
| --------------- | ------ | --------------------- |
| `prompt_length` | int    | prompt 长度（非内容） |
| `request_id`    | string | 如框架提供            |

---

## 5. 禁止记录字段

| 字段                       | 原因             |
| -------------------------- | ---------------- |
| raw prompt 全文            | 隐私             |
| raw LLM response 全文      | 隐私             |
| raw MCP result             | 可能含敏感数据   |
| API key                    | secret           |
| token                      | secret           |
| cookie                     | secret           |
| password                   | secret           |
| request headers            | 可能含 auth 信息 |
| stack trace                | 安全             |
| env                        | 安全             |
| API key owner raw identity | 隐私             |
| full model object          | 安全             |
| full user object           | 隐私             |

---

## 6. 方案 A/B/C 对比

### 方案 A：复用现有 Plane activity/audit infrastructure

| 项目               | 说明                                                            |
| ------------------ | --------------------------------------------------------------- |
| 优点               | 与 Plane 现有模式一致；可复用 `IssueActivity` 模式              |
| 缺点               | 现有基础设施是 issue-scoped，不适合 AI/MCP 场景；需要新建 model |
| 是否需要 migration | 是（新建 `AIAuditEvent` model）                                 |
| 是否适合 Phase 8.1 | ⚠️ 可作为 Phase 8.2                                             |

### 方案 B：使用 Django/Python logger 记录结构化安全日志

| 项目               | 说明                                                                 |
| ------------------ | -------------------------------------------------------------------- |
| 优点               | 不需要 migration；不依赖数据库；日志可由运维工具收集和分析；最小改动 |
| 缺点               | 不持久化到数据库；不能通过 API 查询；依赖日志收集基础设施            |
| 是否需要 migration | 否                                                                   |
| 是否适合最小实现   | ✅ 推荐 Phase 8.1                                                    |

### 方案 C：新增专用 AIAuditEvent model

| 项目               | 说明                                                      |
| ------------------ | --------------------------------------------------------- |
| 优点               | 持久化到数据库；可通过 API 查询；可做 admin UI            |
| 缺点               | 需要 migration；增加数据库写入负担；需要数据保留/清理策略 |
| 是否需要 migration | 是                                                        |
| 为什么应后置       | 当前阶段约束不允许新增 migration                          |

### 推荐结论

**Phase 8.1 推荐方案 B**：Python logger 结构化安全日志。

理由：

1. 不需要 migration
2. 不需要修改 Docker
3. 最小改动
4. 与现有 `log_exception()` 和 `RequestLoggerMiddleware` 模式一致
5. 日志可由 ELK/Datadog/CloudWatch 等工具收集和分析
6. 后续可升级到方案 C（数据库持久化 + API 查询）

---

## 7. 推荐 Phase 8.1 实现方案

### 新增文件

```
apps/api/plane/ai/audit.py
```

### 核心函数

```python
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("plane.ai.audit")

def log_ai_event(
    event_type: str,
    workspace_slug: str,
    user_id: str,
    mode: str = "standard",
    adapter: str = "none",
    tool_name: Optional[str] = None,
    tool_status: Optional[str] = None,
    duration_ms: Optional[int] = None,
    item_count: Optional[int] = None,
    error_code: Optional[str] = None,
    source: str = "pi-chat",
) -> None:
    """Log a structured AI/MCP audit event. Never logs secrets."""
    logger.info(json.dumps({
        "event_type": event_type,
        "workspace_slug": workspace_slug,
        "user_id": user_id,
        "mode": mode,
        "adapter": adapter,
        "tool_name": tool_name,
        "tool_status": tool_status,
        "readonly": True,
        "permission_filtered": True,
        "duration_ms": duration_ms,
        "item_count": item_count,
        "error_code": error_code,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }))
```

### 调用点

| 位置                               | 事件                     |
| ---------------------------------- | ------------------------ |
| `execute_mcp_request()` 入口       | `ai.request`             |
| `execute_mcp_request()` mock 成功  | `ai.tool.call` (success) |
| `execute_mcp_request()` stdio 成功 | `ai.tool.call` (success) |
| `execute_mcp_request()` blocked    | `ai.tool.blocked`        |
| `execute_mcp_request()` error      | `ai.tool.error`          |
| stdio permission gate 拒绝         | `ai.tool.rejected`       |
| 写操作被拒绝                       | `ai.tool.rejected`       |
| endpoint mode=standard             | `ai.request`             |

---

## 8. 是否需要 migration

**Phase 8.1 不需要。** 方案 B 使用 Python logger。

Phase 8.2（数据库持久化）需要 migration。

---

## 9. 是否需要 Docker

**否。** Python logger 输出到 stdout/stderr，由容器运行时收集。

---

## 10. 是否需要前端 audit UI

**Phase 8.1 不需要。**

建议：

- Phase 8.1：只写服务端结构化日志
- Phase 8.2（后续）：新增数据库持久化 model + migration
- Phase 8.3（后续）：admin-only audit log 查看页面

---

## 11. 权限建议

| 阶段      | 查看方式              | 权限        |
| --------- | --------------------- | ----------- |
| Phase 8.1 | 服务端日志文件/stdout | 运维/管理员 |
| Phase 8.2 | API endpoint          | ADMIN only  |
| Phase 8.3 | 前端 UI               | ADMIN only  |

---

## 12. 隐私与安全要求

| 要求                          | 实现                    |
| ----------------------------- | ----------------------- |
| 不记录 raw prompt             | ✅ 只记录 prompt_length |
| 不记录 raw result             | ✅ 只记录 item_count    |
| 不记录 secret                 | ✅ 字段白名单           |
| 不记录 headers                | ✅ 不在 schema 中       |
| 不记录 stack trace            | ✅ 只记录 error_code    |
| 不记录 env                    | ✅ 不在 schema 中       |
| 不记录 API key owner identity | ✅ 使用 request.user    |
| 错误 code 化                  | ✅ 定义标准 error_code  |
| 写操作记录为 rejected         | ✅ 不执行               |

---

## 13. 是否可以进入 Phase 8.1

**是。** 调研完成，方案确定（方案 B：Python logger）。

---

## 14. 是否可以进入写操作阶段

**否。** 建议先完成 audit logging，再考虑写操作。

---

## 15. Phase 8.1 实施记录（2026-05-28）

Phase 8.1 已按本文档方案 B 实施，详见 [`PHASE_8_1_MINIMAL_AUDIT_LOGGING_REPORT.md`](./PHASE_8_1_MINIMAL_AUDIT_LOGGING_REPORT.md)。

**实施结果**：

- ✅ 新增 `apps/api/plane/ai/audit_logger.py`（`plane.ai.audit` logger）
- ✅ 结构化 JSON 日志事件
- ✅ 不记录 raw prompt / raw result / secret
- ✅ 错误使用 error_code
- ✅ 不需要 migration
