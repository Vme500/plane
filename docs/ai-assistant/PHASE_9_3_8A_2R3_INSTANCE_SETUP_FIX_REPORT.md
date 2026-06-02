# 第 9.3.8A-2R3 阶段报告：Instance Setup Fix

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：修复完成

---

## 1. 当前分支和 commit

| 项目        | 值                                                   |
| ----------- | ---------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`               |
| 最新 commit | `f27e345fbd` — `docs: diagnose AI dev web API proxy` |
| 工作区状态  | 有未提交 docs 报告                                   |

---

## 2. 用户问题

`/god-mode` 显示 "Welcome to Plane / Get started"，点击后无变化。

---

## 3. /api/instances/ 关键状态

| 字段                        | 修复前  | 修复后 |
| --------------------------- | ------- | ------ |
| `is_setup_done`             | `false` | `true` |
| `is_signup_screen_visited`  | `false` | `true` |
| `is_email_password_enabled` | `true`  | `true` |
| `workspaces_exist`          | `true`  | `true` |

---

## 4. God-mode/setup 代码定位

| 文件                                                   | 说明                                                                 |
| ------------------------------------------------------ | -------------------------------------------------------------------- |
| `apps/web/core/lib/wrappers/instance-wrapper.tsx:45`   | `if (instance?.is_setup_done === false) return <InstanceNotReady />` |
| `apps/web/core/components/instance/not-ready-view.tsx` | 渲染 "Welcome to Plane" + "Get started"                              |
| `apps/api/plane/license/api/views/admin.py:231`        | `instance.is_setup_done = True`（setup 完成时设置）                  |
| `apps/api/plane/license/models/instance.py:38`         | `is_setup_done = models.BooleanField(default=False)`                 |

---

## 5. Root Cause

超级用户通过 Django shell 创建，绕过了 Plane 的官方 setup 流程。`is_setup_done` 和 `is_signup_screen_visited` 仍为 `False`，导致前端显示 `InstanceNotReady` 页面。

---

## 6. 修复方案

**方案 C：修改 isolated dev DB 的 instance setup flags。**

通过 Django shell 设置：

- `instance.is_setup_done = True`
- `instance.is_signup_screen_visited = True`
- 创建 `InstanceAdmin` 记录

---

## 7. 是否修改 isolated dev DB

**是。** 只修改 instance 配置字段。

---

## 8. 修改字段清单

| 字段                       | 值       |
| -------------------------- | -------- |
| `is_setup_done`            | `True`   |
| `is_signup_screen_visited` | `True`   |
| `InstanceAdmin`            | 创建记录 |

---

## 9. 是否重启 dev stack

**是。** API 和 Worker 已重启。

---

## 10. issue state 是否仍为 Todo

**✅ 是。**

---

## 11. 是否存在 ai.write.executed

**否。**

---

## 12. 是否可以进入 Phase 9.3.8A-3

**是。** 用户现在应该能进入登录页面。
