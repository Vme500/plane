# 第 8.8 阶段报告：AI Audit Retention Management Command Implementation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                       |
| ---------- | -------------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                   |
| 基于       | `7f6fbc5b12` — `docs: design AI audit retention command` |
| 工作区状态 | 干净（无未提交修改）                                     |

---

## 2. 修改文件清单

| 文件                                                               | 变更                     |
| ------------------------------------------------------------------ | ------------------------ |
| `apps/api/plane/db/management/commands/cleanup_ai_audit_events.py` | 新增：management command |

---

## 3. command 文件路径

`apps/api/plane/db/management/commands/cleanup_ai_audit_events.py`

---

## 4. 命令名

```
python manage.py cleanup_ai_audit_events
```

---

## 5. 参数清单

| 参数               | 类型 | 默认值 | 说明                    |
| ------------------ | ---- | ------ | ----------------------- |
| `--days`           | int  | 90     | 保留天数（最小 7）      |
| `--workspace-slug` | str  | None   | 可选，按 workspace 清理 |
| `--batch-size`     | int  | 1000   | 每批删除数量（1-10000） |
| `--confirm`        | flag | False  | 显式确认删除            |

---

## 6. 默认 retention days

90 天

---

## 7. 最小 retention days

7 天（低于此值报 CommandError）

---

## 8. dry-run 行为

- 不删除任何记录
- 统计 cutoff 之前的记录数量
- 输出 cutoff 时间、匹配总数、workspace slug（如有）
- 不输出事件详情、actor email、raw prompt/result/secret

---

## 9. confirm 删除行为

- hard delete（物理删除）
- 按 batch 删除（默认 1000/batch）
- 每批输出删除数量
- 最后输出总删除数量

---

## 10. hard delete 实现方式

使用 `AIAuditEvent.all_objects.filter(...).delete()`：

- `all_objects` 返回所有记录（含 soft-deleted）
- queryset `.delete()` 绕过 model 的 `delete(soft=True)` 方法
- 直接执行 SQL DELETE（hard delete）

---

## 11. batch 删除方式

```python
while True:
    batch_ids = list(qs.order_by("created_at").values_list("id", flat=True)[:batch_size])
    if not batch_ids:
        break
    AIAuditEvent.all_objects.filter(id__in=batch_ids).delete()
```

---

## 12. 安全输出字段

- cutoff datetime
- days
- dry-run / confirm 状态
- workspace slug
- matched count
- deleted count
- batch count

---

## 13. 禁止输出字段

raw prompt, raw result, raw MCP result, token, API key, cookie, password, headers, stack trace, env, actor email, event details。

---

## 14. 是否新增 migration

**否。**

---

## 15. 是否修改 Docker

**否。**

---

## 16. 是否新增前端 UI

**否。**

---

## 17. 是否新增 API

**否。**

---

## 18. 是否实现写操作

**否。** 只是数据清理，不是业务写操作。

---

## 19. 是否运行 migrate

**否。**

---

## 20. 是否执行真实删除

**否。** 命令已实现，但本次未执行任何删除操作。

---

## 21. py_compile 结果

| 文件                                                               | 结果    |
| ------------------------------------------------------------------ | ------- |
| `apps/api/plane/db/management/commands/cleanup_ai_audit_events.py` | ✅ 通过 |
| `apps/api/plane/db/models/ai.py`                                   | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`                                | ✅ 通过 |
| `apps/api/plane/app/serializers/ai.py`                             | ✅ 通过 |
| `apps/api/plane/app/views/ai.py`                                   | ✅ 通过 |

---

## 22. help/dry-run 检查结果

未执行（环境缺少 Django 依赖）。command 基于现有项目模式实现，py_compile 通过。

---

## 23. grep 安全检查结果

无敏感字段命中。command 只输出统计数量，不输出事件详情。

---

## 24. 已知限制

| 问题                   | 说明                     |
| ---------------------- | ------------------------ |
| 未在真实环境测试       | 当前环境缺少 Django 依赖 |
| 未实现 `--before` 参数 | 后续可扩展               |
| 无自动调度             | 需手动执行或配置 cron    |

---

## 25. Phase 8.8.5 验证建议

- 在完整 Django 环境中执行 `--help` 验证参数
- 执行 dry-run 验证统计输出
- 验证 `--days 7` 最小保留期保护
- 验证 `--batch-size` 范围检查
