# 第 9.3.8A-2R2 阶段报告：Web API Proxy Verification

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：代理已生效，需用户验证浏览器

---

## 1. 当前分支和 commit

| 项目        | 值                                                            |
| ----------- | ------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                        |
| 最新 commit | `d399f4592a` — `fix: enable isolated AI dev web auth methods` |
| 工作区状态  | 干净                                                          |

---

## 2. 18180/api/instances/ 返回结果

✅ JSON，`is_email_password_enabled: true`

---

## 3. 18181/api/instances/ 返回结果

✅ JSON（通过 nginx proxy），`is_email_password_enabled: true`

---

## 4. nginx-dev.conf 是否实际生效

**✅ 是。** `nginx -T` 确认容器内加载了正确的配置，包含 `/api/` 和 `/auth/` proxy。

---

## 5. Root Cause 分析

代理已生效，API 返回正确数据。用户看到 "No authentication methods available" 的可能原因：

1. **浏览器缓存**：旧 SPA HTML/JS 被缓存，未清除
2. **SWR 缓存**：前端 SWR 缓存了旧的 API 响应
3. **is_setup_done=false**：API 返回 `is_setup_done: false`，前端可能先显示 `InstanceNotReady`，然后跳转到 auth 页时 config 未加载

---

## 6. 修复状态

| 修复             | 状态                                 |
| ---------------- | ------------------------------------ |
| nginx API proxy  | ✅ 已生效                            |
| API 返回正确配置 | ✅ `is_email_password_enabled: true` |
| 浏览器验证       | ⚠️ 待用户确认                        |

---

## 7. 用户验证步骤

请执行以下步骤：

1. **关闭所有浏览器窗口**（不仅仅是标签页）
2. **重新打开浏览器**
3. **打开无痕/隐私窗口**
4. **访问 http://localhost:18181**
5. **观察页面**：
   - 如果看到 "Welcome to Plane" + "Get started" 按钮 → 点击 "Get started"
   - 如果看到登录表单 → 说明修复成功
   - 如果仍看到 "No authentication methods available" → 截图并反馈

6. **不要登录**
7. **不要进入 pi-chat**
8. **不要输入 UUID 指令**

---

## 8. issue state 是否仍为 Todo

**✅ 是。**

---

## 9. 是否存在 ai.write.executed

**否。**

---

## 10. 是否可以进入 Phase 9.3.8A-3

**有条件。** 需要用户确认 Web UI 显示登录表单。

---

## 11. Phase 9.3.8A-2R3 修复记录（2026-06-02）

Phase 9.3.8A-2R3 修复了 instance setup blocker，详见 [`PHASE_9_3_8A_2R3_INSTANCE_SETUP_FIX_REPORT.md`](./PHASE_9_3_8A_2R3_INSTANCE_SETUP_FIX_REPORT.md)。

**修复**：

- `is_setup_done=True`
- `is_signup_screen_visited=True`
- 创建 `InstanceAdmin` 记录
