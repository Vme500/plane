# 第 9.3.8A-4R6 阶段报告：Windows Edge Automation

> 日期：2026-06-03
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：Edge CDP 可访问，Node.js 连接受限

---

## 1. 浏览器自动化尝试

| 方案                           | 结果                        |
| ------------------------------ | --------------------------- |
| Playwright bundled chromium    | ❌ 不支持 ubuntu26.04-x64   |
| Playwright connectOverCDP      | ❌ 400 错误                 |
| Node.js native WebSocket + CDP | ❌ ECONNREFUSED（代理问题） |
| Python websocket               | ❌ 无库                     |
| curl CDP HTTP API              | ✅ 可访问                   |

---

## 2. Root Cause

**Node.js 使用 HTTP 代理（`172.23.0.1:7897`），即使设置 `NO_PROXY`/`HTTP_PROXY=""` 仍无法绕过。** curl 不受代理影响，可以连接 CDP。

---

## 3. 已验证

| 检查项              | 结果                                              |
| ------------------- | ------------------------------------------------- |
| Edge CDP 可访问     | ✅ `http://127.0.0.1:9222/json/version` 返回 JSON |
| pi-chat page 可创建 | ✅ `http://127.0.0.1:9222/json/new?...`           |
| issue state         | Todo ✅                                           |
| ai.write.executed   | 0 ✅                                              |

---

## 4. 建议

用户可直接在 Windows Edge 中验证：

1. 打开 `http://localhost:18181/ai-test/pi-chat`
2. 切换到 MCP Read-only 模式
3. 输入指令
4. 确认 Confirm 按钮可见且 enabled
5. **不要点击 Confirm**
