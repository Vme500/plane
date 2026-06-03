# 第 9.3.8A-4R5 阶段报告：Autonomous Confirm Button Visibility Fix

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：修复完成，Confirm button 强制可见

---

## 1. 浏览器自动化尝试

| 方案                             | 结果                      |
| -------------------------------- | ------------------------- |
| Playwright bundled chromium      | ❌ 不支持 ubuntu26.04-x64 |
| Playwright connectOverCDP (Edge) | ❌ CDP 400 错误           |
| Python websocket CDP             | ❌ 无 websocket 库        |
| 临时诊断 UI                      | ✅ 已部署但用户未验证     |

---

## 2. 修复方案

**前端最小安全修复：Confirm button 始终渲染。**

重写 confirmation card 操作区：

- `canConfirm = executionEnabled && confirmationTokenPresent`
- Confirm button 始终显示
- `disabled={!canConfirm}`
- 显示安全诊断行：`req`, `exec`, `token`, `can_confirm`, `disabled_reason`
- 原 onClick handler 保留在 `false &&` 块中（不执行）

---

## 3. 修改文件清单

| 文件                                                             | 变更                         |
| ---------------------------------------------------------------- | ---------------------------- |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | 重写 Confirm button 渲染逻辑 |

---

## 4. 新渲染逻辑

```tsx
const requiresConfirmation = Boolean(pa?.requires_confirmation);
const executionEnabled = Boolean(pa?.execution_enabled);
const confirmationTokenPresent = Boolean(pa?.confirmation_token);
const canConfirm = executionEnabled && confirmationTokenPresent;

// Confirm button always visible, disabled when !canConfirm
<button disabled={!canConfirm}>Confirm</button>;
```

---

## 5. 安全诊断行显示

```
req=true | exec=true | token=true | can_confirm=true
```

或当条件不满足时：

```
req=true | exec=false | token=true | can_confirm=false | reason=execution_not_enabled
```

---

## 6. 验证结果

| 检查项                          | 结果    |
| ------------------------------- | ------- |
| Web 容器包含 `can_confirm` 代码 | ✅      |
| issue state                     | Todo ✅ |
| ai.write.executed               | 0 ✅    |
| confirmation_token 值未显示     | ✅      |
