# 第 9.3.8A-2R5 阶段报告：CSRF Login Fix

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：修复完成

---

## 1. 当前分支和 commit

| 项目        | 值                                                               |
| ----------- | ---------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                           |
| 最新 commit | `7c8031a598` — `docs: diagnose isolated AI dev API 502 recovery` |
| 工作区状态  | 有未提交修复                                                     |

---

## 2. 用户问题

登录提交后显示 "CSRF Verification Failed"。

---

## 3. Root Cause

**`CSRF_TRUSTED_ORIGINS` 为空。**

浏览器从 `http://localhost:18181` 提交表单，但 API 在 `http://localhost:18180`。Django CSRF 中间件要求 `CSRF_TRUSTED_ORIGINS` 包含请求的 Origin，否则拒绝。

---

## 4. 修复

添加 `CSRF_TRUSTED_ORIGINS=http://localhost:18181` 和 `CORS_ALLOWED_ORIGINS=http://localhost:18181` 到环境变量。

---

## 5. 修改文件清单

| 文件                  | 变更                    |
| --------------------- | ----------------------- |
| `.env.ai-dev.example` | 添加 CSRF/CORS 环境变量 |
| `.env.ai-dev.local`   | 添加 CSRF/CORS 环境变量 |

---

## 6. 修复后验证

| 检查项                 | 结果                        |
| ---------------------- | --------------------------- |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:18181` ✅ |
| API 18180              | 200 ✅                      |
| Web proxy 18181        | 200 ✅                      |

---

## 7. 是否可以进入 Phase 9.3.8A-3

**是。** CSRF 配置已修复，用户应能正常登录。
