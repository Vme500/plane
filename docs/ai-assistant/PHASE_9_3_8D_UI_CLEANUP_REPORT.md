# 第 9.3.8D 阶段报告：UI Cleanup and Production-Readiness

> 日期：2026-06-03
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：清理完成

---

## 1. Cleanup 目标

移除临时诊断行，改进文案，保留安全逻辑。

---

## 2. 修改文件清单

| 文件                                                             | 变更                 |
| ---------------------------------------------------------------- | -------------------- |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | 移除诊断行，改进文案 |

---

## 3. 诊断行处理

**已移除。** `req/exec/token/can_confirm` 诊断行不再显示。

---

## 4. Confirm 按钮文案

**"Confirm"** ✅

---

## 5. Plan only 文案

**改为 "Confirmation required"** ✅

---

## 6. Confirm button 可视修复

**保留。** Inline styles 确保按钮可见。

---

## 7. canConfirm 安全逻辑

**保持。** `canConfirm = executionEnabled && confirmationTokenPresent`，`disabled={!canConfirm}`。

---

## 8-9. confirmation_token

未显示 ✅，未输出 ✅

---

## 10. 是否改变 Confirm execution path

**否。**

---

## 11. 是否改变 permission / TimestampSigner / audit

**否。**

---

## 12. Smoke test 结果

| 检查项                              | 结果           |
| ----------------------------------- | -------------- |
| Bundle 包含 "Confirmation required" | ✅             |
| 诊断行已移除                        | ✅             |
| issue state                         | In Progress ✅ |
| ai.write.executed                   | 1 ✅           |
