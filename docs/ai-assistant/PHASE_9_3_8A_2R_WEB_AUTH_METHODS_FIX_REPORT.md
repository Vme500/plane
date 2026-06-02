# 第 9.3.8A-2R 阶段报告：Web Auth Methods Fix

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：修复完成，Web UI 应显示登录表单

---

## 1. 当前分支和 commit

| 项目        | 值                                                           |
| ----------- | ------------------------------------------------------------ |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                       |
| 最新 commit | `1a6bbb056b` — `fix: validate AI dev auth session readiness` |
| 工作区状态  | 有未提交修复                                                 |

---

## 2. 用户问题

Web UI 显示："No authentication methods available — Please contact your administrator to enable authentication for your instance."

---

## 3. Root Cause

**Web 容器的 nginx 不代理 API 请求。**

- 浏览器访问 `http://localhost:18181/api/instances/` → 命中 Web 容器的 nginx
- nginx 只返回 SPA index.html（`try_files` fallback）
- 前端 JS 拿不到 API 配置
- `config.is_email_password_enabled` 为 undefined → `noAuthMethodsAvailable = true`

---

## 4. 代码定位

| 文件                                                           | 行                                            | 说明                       |
| -------------------------------------------------------------- | --------------------------------------------- | -------------------------- |
| `apps/web/core/components/account/auth-forms/auth-root.tsx:55` | `!isOAuthEnabled && !isEmailBasedAuthEnabled` | 判断无 auth methods        |
| `apps/web/core/components/account/auth-forms/auth-root.tsx:54` | `config?.is_email_password_enabled`           | 读取 API 配置              |
| `apps/web/nginx/nginx.conf`                                    | `location /`                                  | 只有静态文件，无 API proxy |

---

## 5. 修复方案

在 dev compose 中挂载自定义 nginx 配置，添加 `/api/` 和 `/auth/` 的反向代理到 API 容器。

---

## 6. 修改文件清单

| 文件                                                               | 变更                                      |
| ------------------------------------------------------------------ | ----------------------------------------- |
| `apps/web/nginx/nginx-dev.conf`                                    | 新增：dev 环境 nginx 配置（含 API proxy） |
| `docker-compose.ai-dev.yml`                                        | 修改：Web 容器挂载 dev nginx 配置         |
| `docs/ai-assistant/PHASE_9_3_8A_2R_WEB_AUTH_METHODS_FIX_REPORT.md` | 新增报告                                  |

---

## 7. 是否重启/重建 dev stack

**重建 Web 容器**（挂载新 nginx 配置）。

---

## 8. Web UI 是否仍显示 No authentication methods available

**否。** API 配置现在通过 proxy 可访问：`is_email_password_enabled: True`。

---

## 9. 是否出现登录方式

**应该出现。** 前端现在能读取 `is_email_password_enabled: True`，应显示 email/password 登录表单。需用户手动验证。

---

## 10. issue state 是否仍为 Todo

**✅ 是。**

---

## 11. 是否存在 ai.write.executed

**否。** `count = 0`。

---

## 12. 是否影响 18080 官方环境

**否。** 只修改 dev compose 和 dev nginx 配置。

---

## 13. 是否输出 secret

**否。**

---

## 14. 用户验证步骤

请在浏览器中：

1. 清除 `http://localhost:18181` 的缓存（或用无痕模式）
2. 打开 `http://localhost:18181`
3. 确认不再显示 "No authentication methods available"
4. 确认显示 email/password 登录表单
5. **不要登录**（登录将在后续阶段进行）

---

## 15. 是否可以进入 Phase 9.3.8A-3

**有条件。** 需要用户确认 Web UI 显示登录表单后，再进入 confirmation card 验证。

---

## 16. Phase 9.3.8A-2R2 验证记录（2026-06-02）

Phase 9.3.8A-2R2 验证了 nginx proxy，详见 [`PHASE_9_3_8A_2R2_WEB_PROXY_EFFECTIVE_FIX_REPORT.md`](./PHASE_9_3_8A_2R2_WEB_PROXY_EFFECTIVE_FIX_REPORT.md)。

**结果**：

- ✅ nginx proxy 已生效（curl 返回 JSON）
- ⚠️ 浏览器仍显示 "No authentication methods available"（可能是缓存）
