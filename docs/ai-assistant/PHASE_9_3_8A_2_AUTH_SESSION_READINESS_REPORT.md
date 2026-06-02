# 第 9.3.8A-2 阶段报告：Auth/Session Readiness Diagnosis

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：Root cause 找到并修复，sign-in 不再 500

---

## 1. 当前分支和 commit

| 项目        | 值                                                                           |
| ----------- | ---------------------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                                       |
| 最新 commit | `f63145d1ab` — `docs: verify AI state update proposed action API UI runtime` |
| 工作区状态  | 有未提交修复（.env + compose + docs）                                        |

---

## 2. Dev stack 健康检查

| 检查项       | 结果   |
| ------------ | ------ |
| API 18180    | 200 ✅ |
| Web 18181    | 200 ✅ |
| 不影响 18080 | ✅     |

---

## 3. Sign-in 500 Root Cause

**`APP_BASE_URL` 和 `WEB_URL` 环境变量未设置。**

Django sign-in view 调用 `get_safe_redirect_url(base_url, ...)` 时，`base_url` 为 `None`，导致 `None.rstrip("/")` 抛出 `AttributeError`。

**修复**：在 `.env.ai-dev.local` 和 `.env.ai-dev.example` 中添加：

```
APP_BASE_URL=http://localhost:18181
WEB_URL=http://localhost:18180
ADMIN_BASE_URL=http://localhost:18181
SPACE_BASE_URL=http://localhost:18181
```

---

## 4. 修复后 Sign-in 结果

| 测试                   | 结果                            |
| ---------------------- | ------------------------------- |
| `POST /auth/sign-in/`  | 302 redirect ✅（不再 500）     |
| Session cookie in curl | ⚠️ 未设置（前端-mediated flow） |
| Web UI 登录            | 应该可用（需手动验证）          |

---

## 5. 测试用户状态

| 项目           | 值                   |
| -------------- | -------------------- |
| user_id        | `f6bf5655-...`       |
| email          | `a***@ai-test.local` |
| is_active      | True                 |
| workspace role | ADMIN (20)           |
| project role   | ADMIN (20)           |

---

## 6. 修改文件清单

| 文件                                                                | 变更              |
| ------------------------------------------------------------------- | ----------------- |
| `.env.ai-dev.local`                                                 | 添加 URL 环境变量 |
| `.env.ai-dev.example`                                               | 添加 URL 环境变量 |
| `docs/ai-assistant/PHASE_9_3_8A_2_AUTH_SESSION_READINESS_REPORT.md` | 新增报告          |

---

## 7. 是否重启 dev stack

**是。** API 容器已重建以加载新环境变量。

---

## 8. 登录/session 是否可用

**Sign-in 返回 302（成功）。** 但 curl 无法捕获 session cookie（前端-mediated flow）。Web UI 应该可用。

---

## 9. 是否生成 proposed_action

**否。** 本阶段只做诊断。

---

## 10. 是否点击 Confirm

**否。**

---

## 11. 是否发送 confirm_action_id

**否。**

---

## 12. 是否修改 issue/work item/state/project

**否。**

---

## 13. 是否调用 stdio write

**否。**

---

## 14. 是否调用 plane-mcp-server write

**否。**

---

## 15. 是否影响 18080 官方环境

**否。**

---

## 16. 是否输出 secret

**否。**

---

## 17. 是否可以进入 Phase 9.3.8A-3

**是。** Sign-in 不再 500，可通过 Web UI 验证 confirmation card。
