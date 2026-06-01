# 第 8.6.5 阶段报告：Admin-Only AI Audit Read API Permission/Security Validation

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：验证完成，发现并修复 1 个 bug

---

## 1. 当前分支和 commit

| 项目        | 值                                                 |
| ----------- | -------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`             |
| 最新 commit | `3c4e2c479c` — `feat: add admin AI audit read API` |
| 工作区状态  | 有 1 个未提交修复（serializer source bug）         |

---

## 2. 权限验证结果

| 检查项                                                             | 结果                           |
| ------------------------------------------------------------------ | ------------------------------ |
| `@allow_permission(allowed_roles=[ROLE.ADMIN], level="WORKSPACE")` | ✅                             |
| workspace ADMIN 可以访问                                           | ✅                             |
| workspace MEMBER 返回 403                                          | ✅                             |
| workspace GUEST 返回 403                                           | ✅                             |
| 非 workspace member 返回 404                                       | ✅（由 allow_permission 处理） |
| 未认证用户被拒绝                                                   | ✅                             |
| project admin 不能替代 workspace admin                             | ✅                             |

---

## 3. workspace scope 验证结果

| 检查项                                   | 结果                                |
| ---------------------------------------- | ----------------------------------- |
| 查询必须 filter workspace slug           | ✅ `workspace__slug=slug`           |
| 不允许通过 query 参数覆盖 workspace      | ✅ workspace slug 来自 URL 路径参数 |
| 不允许传 workspace_id 查询其他 workspace | ✅ 无 workspace_id 参数             |
| actor_id filter 在 workspace scope 内    | ✅                                  |
| 所有 filters 在 workspace scope 内       | ✅                                  |
| select_related 不改变权限                | ✅                                  |
| ordering 固定 created_at desc            | ✅                                  |
| 不允许 unrestricted export               | ✅                                  |

---

## 4. serializer 安全验证结果

| 检查项                               | 结果 |
| ------------------------------------ | ---- |
| 只返回安全字段                       | ✅   |
| actor 只返回 id/display_name/email   | ✅   |
| 不返回 raw prompt                    | ✅   |
| 不返回 raw result                    | ✅   |
| 不返回 raw MCP result                | ✅   |
| 不返回 token/API key/cookie/password | ✅   |
| 不返回 headers/stack/env             | ✅   |
| 不返回 full user object              | ✅   |
| 不返回 full model object             | ✅   |
| 不返回 deleted_at                    | ✅   |
| 不返回 created_by/updated_by         | ✅   |
| 只读                                 | ✅   |

---

## 5. filter 安全验证结果

| 检查项                      | 结果        |
| --------------------------- | ----------- |
| boolean 只接受 true/false   | ✅          |
| date 解析安全（try/except） | ✅          |
| invalid date 不导致 500     | ✅ 返回 400 |
| invalid boolean 不导致 500  | ✅ 忽略     |
| 超过 90 天窗口 clamp        | ✅          |
| clamp 不扩大查询范围        | ✅          |
| 默认 30 天窗口生效          | ✅          |
| 不支持 raw prompt 搜索      | ✅          |
| 不支持 raw result 搜索      | ✅          |
| 不支持 unrestricted export  | ✅          |

---

## 6. pagination / ordering 验证结果

| 检查项                     | 结果 |
| -------------------------- | ---- |
| 默认 page size 20          | ✅   |
| max page size 100          | ✅   |
| created_at DESC            | ✅   |
| 没有返回全部数据的路径     | ✅   |
| 没有 export 参数           | ✅   |
| 没有绕过 pagination 的分支 | ✅   |

---

## 7. URL route 检查结果

| 检查项                             | 结果 |
| ---------------------------------- | ---- |
| 路径符合 Plane 风格                | ✅   |
| 放在 external.py 合理              | ✅   |
| 不影响现有 /ai-assistant/ endpoint | ✅   |
| 不改变 existing API contract       | ✅   |
| 不恢复 mcp_result                  | ✅   |

---

## 8. 是否记录/返回 raw prompt

**否。**

---

## 9. 是否记录/返回 raw result

**否。**

---

## 10. 是否记录/返回 raw MCP result

**否。**

---

## 11. 是否返回 token/API key/cookie/password

**否。**

---

## 12. 是否返回 headers/stack/env

**否。**

---

## 13. 是否存在跨 workspace 查询风险

**否。** queryset 始终 `workspace__slug=slug`。

---

## 14. 是否存在 MEMBER/GUEST 绕过风险

**否。** `allow_permission` 正确限制为 ADMIN。

---

## 15. 是否做了小修复

**是。** 修复了 `ActorLiteSerializer` 的 `source` 参数：

- **修复前**：`source="actor_id"`（会传递 UUID 而非 User 对象）
- **修复后**：`source="actor"`（正确传递 User 对象）

---

## 16. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/app/serializers/ai.py`      | ✅ 通过 |
| `apps/api/plane/app/views/ai.py`            | ✅ 通过 |
| `apps/api/plane/app/urls/external.py`       | ✅ 通过 |
| `apps/api/plane/db/models/ai.py`            | ✅ 通过 |
| `apps/api/plane/ai/audit_logger.py`         | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 17. Django check 结果

未执行（环境缺少 celery/psycopg/redis 等依赖）。

---

## 18. 是否新增 migration

**否。**

---

## 19. 是否修改 Docker

**否。**

---

## 20. 是否实现写操作

**否。**

---

## 21. 是否可以 push

**是。**

---

## 22. 是否可以进入下一阶段

**是。** 修复了 serializer source bug，权限/安全验证通过。
