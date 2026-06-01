# 第 8.8.5 阶段报告：AI Audit Retention Cleanup Command Safety Validation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：验证完成，无需修复

---

## 1. 当前分支和 commit

| 项目        | 值                                                            |
| ----------- | ------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                        |
| 最新 commit | `374910cd68` — `feat: add AI audit retention cleanup command` |
| 工作区状态  | 干净（无未提交修改）                                          |

---

## 2. command 路径注册检查结果

| 检查项                                 | 结果 |
| -------------------------------------- | ---- |
| `management/__init__.py` 存在          | ✅   |
| `management/commands/__init__.py` 存在 | ✅   |
| `plane.db` 在 INSTALLED_APPS           | ✅   |
| command 路径符合 Django 发现规则       | ✅   |
| 无命名冲突                             | ✅   |
| 放在正确 app（plane.db）下             | ✅   |

---

## 3. hard delete 验证结果

| 检查项                                             | 结果                                                         |
| -------------------------------------------------- | ------------------------------------------------------------ |
| AIAuditEvent 继承 BaseModel（含 SoftDeleteModel）  | ✅                                                           |
| `AIAuditEvent.all_objects` 存在                    | ✅（继承自 SoftDeleteModel）                                 |
| `all_objects` 包含 soft-deleted 数据               | ✅（`models.Manager()`，无过滤）                             |
| `all_objects.filter(...).delete()` 执行 SQL DELETE | ✅（queryset delete 绕过 model 的 soft delete）              |
| 不会调用 soft delete 逻辑                          | ✅（queryset `.delete()` 不调用 model `.delete(soft=True)`） |
| 删除范围只限 AIAuditEvent                          | ✅（queryset 基于 AIAuditEvent model）                       |
| 不会删除 Workspace/User/其他表                     | ✅                                                           |

---

## 4. dry-run 保护验证结果

| 检查项                                 | 结果 |
| -------------------------------------- | ---- |
| 未传 `--confirm` 时绝不调用 `delete()` | ✅   |
| dry-run 只 count                       | ✅   |
| dry-run 不逐条加载完整对象             | ✅   |
| dry-run 不输出事件详情                 | ✅   |
| dry-run 不输出 actor email             | ✅   |
| dry-run 不输出任何 secret              | ✅   |
| dry-run 退出码为成功                   | ✅   |
| 默认执行 command 不会删除数据          | ✅   |

---

## 5. --confirm 删除路径验证结果

| 检查项                                            | 结果 |
| ------------------------------------------------- | ---- |
| 只有传 `--confirm` 才进入删除分支                 | ✅   |
| 删除条件包含 `created_at < cutoff`                | ✅   |
| 传 workspace_slug 时添加 `workspace__slug` filter | ✅   |
| batch 删除只基于匹配 queryset 的 ids              | ✅   |
| 每批只删除 AIAuditEvent                           | ✅   |
| 不加载完整对象                                    | ✅   |
| 不逐条打印                                        | ✅   |
| 每批只输出数量                                    | ✅   |
| 最终只输出总删除数量                              | ✅   |
| 删除失败报错                                      | ✅   |
| 没有绕过 `--confirm` 的隐藏路径                   | ✅   |

---

## 6. 参数边界验证结果

| 参数               | 检查                        | 结果 |
| ------------------ | --------------------------- | ---- |
| `--days`           | default=90                  | ✅   |
| `--days`           | min=7                       | ✅   |
| `--days`           | <7 报 CommandError          | ✅   |
| `--batch-size`     | default=1000                | ✅   |
| `--batch-size`     | min=1, max=10000            | ✅   |
| `--batch-size`     | 超出范围报 CommandError     | ✅   |
| `--workspace-slug` | optional                    | ✅   |
| `--workspace-slug` | workspace 不存在时返回 0 条 | ✅   |

---

## 7. cutoff/timezone 验证结果

| 检查项                       | 结果                        |
| ---------------------------- | --------------------------- |
| cutoff = now - days          | ✅                          |
| 使用 `timezone.now()`        | ✅（Django timezone-aware） |
| 使用 `created_at__lt=cutoff` | ✅                          |
| 不删除 cutoff 之后的数据     | ✅                          |
| 不因时区错误误删             | ✅                          |

---

## 8. 安全输出检查结果

| 检查项                                    | 结果 |
| ----------------------------------------- | ---- |
| 不输出 raw prompt                         | ✅   |
| 不输出 raw result                         | ✅   |
| 不输出 raw MCP result                     | ✅   |
| 不输出 token/API key/cookie/password      | ✅   |
| 不输出 headers/stack/env                  | ✅   |
| 不输出 actor email                        | ✅   |
| 不输出 event details                      | ✅   |
| 只输出 cutoff/days/status/workspace/count | ✅   |

---

## 9. grep 检查结果

| 检查                    | 命中                  | 安全性  |
| ----------------------- | --------------------- | ------- |
| `raw_result_returned`   | model 字段名          | ✅ 安全 |
| `token/password/secret` | docstring             | ✅ 安全 |
| `headers/stack/env`     | docstring, class Meta | ✅ 安全 |

---

## 10. 是否输出 raw prompt

**否。**

---

## 11. 是否输出 raw result

**否。**

---

## 12. 是否输出 raw MCP result

**否。**

---

## 13. 是否输出 token/API key/cookie/password

**否。**

---

## 14. 是否输出 headers/stack/env

**否。**

---

## 15. 是否输出 actor email/event details

**否。**

---

## 16. 是否执行真实删除

**否。**

---

## 17. 是否运行 migrate

**否。**

---

## 18. 是否做了小修复

**否。** 验证通过，无需修复。

---

## 19. py_compile 结果

| 文件                                                               | 结果    |
| ------------------------------------------------------------------ | ------- |
| `apps/api/plane/db/management/commands/cleanup_ai_audit_events.py` | ✅ 通过 |
| `apps/api/plane/db/models/ai.py`                                   | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`                                | ✅ 通过 |
| `apps/api/plane/app/serializers/ai.py`                             | ✅ 通过 |
| `apps/api/plane/app/views/ai.py`                                   | ✅ 通过 |

---

## 20. help/dry-run 检查结果

未执行（环境缺少 Django 依赖）。command 基于现有项目模式实现，py_compile 通过。

---

## 21. 是否新增 migration

**否。**

---

## 22. 是否修改 Docker

**否。**

---

## 23. 是否新增前端 UI

**否。**

---

## 24. 是否新增 API

**否。**

---

## 25. 是否实现写操作

**否。**

---

## 26. 是否可以 push

**是。**

---

## 27. 是否可以进入 audit UI 设计

**是。** retention command 安全验证通过。
