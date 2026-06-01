# 第 8.7 阶段报告：AI Audit Retention Management Command Design

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：设计完成，未写代码

---

## 1. 当前分支和 commit

| 项目        | 值                                                        |
| ----------- | --------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                    |
| 最新 commit | `f0b9a60046` — `fix: validate AI audit read API security` |
| 工作区状态  | 干净（无未提交修改）                                      |

---

## 2. 现有 management command / cleanup 风格调研

### 命令文件位置

`apps/api/plane/db/management/commands/`

### 命令命名风格

| 命令                               | 风格             |
| ---------------------------------- | ---------------- |
| `clear_cache.py`                   | 动词\_名词       |
| `update_deleted_workspace_slug.py` | 动词*形容词*名词 |
| `create_dummy_data.py`             | 动词\_名词       |
| `sync_issue_version.py`            | 动词*名词*名词   |

### 命令基类

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "..."
    def add_arguments(self, parser): ...
    def handle(self, *args, **options): ...
```

### dry-run 风格

`update_deleted_workspace_slug.py` 使用 `--dry-run` 参数，与设计一致。

### Soft delete 机制

| 项目                    | 说明                                                         |
| ----------------------- | ------------------------------------------------------------ |
| `BaseModel.objects`     | `SoftDeletionManager()` — 自动过滤 `deleted_at__isnull=True` |
| `BaseModel.all_objects` | `models.Manager()` — 返回所有记录（含 soft-deleted）         |
| `delete(soft=True)`     | soft delete（设置 `deleted_at`）                             |
| `delete(soft=False)`    | hard delete（物理删除）                                      |

---

## 3. 推荐命令名

```
python manage.py cleanup_ai_audit_events
```

文件路径：`apps/api/plane/db/management/commands/cleanup_ai_audit_events.py`

---

## 4. 参数设计

| 参数               | 类型 | 默认值 | 说明                       |
| ------------------ | ---- | ------ | -------------------------- |
| `--days`           | int  | 90     | 保留天数                   |
| `--workspace-slug` | str  | None   | 可选，按 workspace 清理    |
| `--dry-run`        | flag | True   | 只统计，不删除             |
| `--confirm`        | flag | False  | 显式确认删除               |
| `--batch-size`     | int  | 1000   | 每批删除数量               |
| `--before`         | date | None   | 可选，删除此日期之前的数据 |

### 参数逻辑

1. 默认 `--dry-run`（只统计，不删除）
2. 需要显式 `--confirm` 才执行删除
3. `--before` 优先于 `--days`
4. 最小保留期：7 天（防止误删全部数据）

---

## 5. 默认 retention policy

| 项目       | 值                |
| ---------- | ----------------- |
| 默认保留期 | 90 天             |
| 最小保留期 | 7 天              |
| 默认行为   | dry-run（只统计） |

---

## 6. dry-run / confirm 设计

```
# 只统计（默认）
python manage.py cleanup_ai_audit_events

# 执行删除
python manage.py cleanup_ai_audit_events --confirm

# 按 workspace 清理
python manage.py cleanup_ai_audit_events --workspace-slug my-workspace --confirm

# 自定义保留期
python manage.py cleanup_ai_audit_events --days 30 --confirm

# 指定日期
python manage.py cleanup_ai_audit_events --before 2026-01-01 --confirm
```

---

## 7. hard delete vs soft delete 分析

| 维度                | soft delete   | hard delete     |
| ------------------- | ------------- | --------------- |
| 减少数据库体积      | ❌ 不减少     | ✅ 减少         |
| 符合 retention 目标 | ❌ 数据仍存在 | ✅ 数据真正删除 |
| 隐私合规            | ❌ 未真正删除 | ✅ 符合         |
| 可恢复性            | ✅ 可恢复     | ❌ 不可恢复     |
| 审计需求            | ⚠️ 可能需要   | ⚠️ 可能需要     |

### 推荐

**Phase 8.8 使用 hard delete。**

理由：

1. retention 的目标是隐私和体积控制
2. soft delete 不减少数据库体积
3. audit 数据不需要可恢复性
4. 需要显式 `--confirm` 防止误删

### 实现方式

```python
# 使用 all_objects 包含 soft-deleted 记录
AIAuditEvent.all_objects.filter(
    created_at__lt=cutoff,
).delete()  # hard delete
```

或使用 `delete(soft=False)`。

---

## 8. 查询和 batch 删除设计

```python
from datetime import timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(days=days)

# 按 batch 删除
while True:
    batch_ids = list(
        AIAuditEvent.all_objects.filter(
            created_at__lt=cutoff,
        ).order_by("created_at").values_list("id", flat=True)[:batch_size]
    )
    if not batch_ids:
        break
    deleted_count = AIAuditEvent.all_objects.filter(
        id__in=batch_ids
    ).delete()[0]
    total_deleted += deleted_count
```

### 设计要点

1. 使用 `all_objects` 包含 soft-deleted 记录
2. 按 `created_at` 排序，利用索引 `idx_ai_audit_ws_created`
3. batch 删除防止长事务
4. 不加载完整对象
5. 不逐条打印
6. 只输出数量

---

## 9. 输出日志设计

```
# dry-run 模式
Cleanup AI Audit Events (dry-run)
  Workspace: my-workspace
  Retention: 90 days
  Cutoff: 2026-02-28
  Records to delete: 1,234

# confirm 模式
Cleanup AI Audit Events
  Workspace: my-workspace
  Retention: 90 days
  Cutoff: 2026-02-28
  Deleted: 1,234 records
  Completed.
```

### 安全要求

1. 不输出事件详情
2. 不输出 raw prompt/result
3. 不输出 user email/token/secret
4. 只输出数量和 workspace slug

---

## 10. 安全边界

| 要求                                 | 实现                   |
| ------------------------------------ | ---------------------- |
| 不删除 90 天内数据                   | ✅ cutoff = now - days |
| 不默认执行删除                       | ✅ 默认 dry-run        |
| 不输出敏感字段                       | ✅ 只输出数量          |
| 不输出 raw event payload             | ✅                     |
| 不输出 token/API key/cookie/password | ✅                     |
| 不输出 headers/stack/env             | ✅                     |
| 不修改 AI assistant API contract     | ✅                     |
| 不影响 read API                      | ✅                     |
| 删除失败不破坏业务服务               | ✅ 只影响命令退出码    |

---

## 11. Phase 8.8 实施边界

### Phase 8.8 可以做

- 新增 `cleanup_ai_audit_events` management command
- 支持 `--dry-run`（默认）
- 支持 `--confirm`
- 支持 `--days`（默认 90）
- 支持 `--workspace-slug`
- 支持 `--batch-size`（默认 1000）
- 支持 `--before`
- 最小保留期 7 天保护
- docs
- py_compile

### Phase 8.8 不做

- Docker/cron 自动调度
- Celery beat
- 前端 UI
- export
- 写操作
- 新增 migration
- 运行 migrate
- 真实删除生产数据

---

## 12. 是否新增 migration

**否。**

---

## 13. 是否修改 Docker

**否。**

---

## 14. 是否新增前端 UI

**否。**

---

## 15. 是否实现写操作

**否。**

---

## 16. 是否可以进入 Phase 8.8

**是。** 设计完成，可实现 management command。
