# 第 9.3.8A-3R2 阶段报告：Web UI Internal Error Diagnosis

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：Root cause 找到（用户未切换 MCP 模式）

---

## 1. 当前分支和 commit

| 项目        | 值                                                                  |
| ----------- | ------------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                              |
| 最新 commit | `06bcc33bf2` — `fix: validate AI state update confirmation card UI` |
| 工作区状态  | 干净                                                                |

---

## 2. 用户问题

pi-chat 输入 UUID 指令后显示 "Error: An internal error has occurred."

---

## 3. Root Cause

**用户未切换到 MCP 模式。** 默认模式是 "Standard Chat"，会调用 OpenAI API。由于 `LLM_API_KEY` 是 placeholder (`replace-me`)，OpenAI 返回 401 认证失败。

API 日志：

```
openai.AuthenticationError: Error code: 401 - Incorrect API key provided: replace-me
```

---

## 4. 解决方案

**用户需要先点击 "MCP Read-only" 按钮切换到 MCP 模式，然后再输入指令。**

---

## 5. 修改文件清单

无代码修改。

---

## 6. 用户操作步骤

1. 打开 http://localhost:18181/ai-test/pi-chat
2. 在输入框上方找到 "Mode:" 区域
3. 点击 **"MCP Read-only"** 按钮（不要用 "Standard Chat"）
4. 确认按钮高亮且显示 "Read-only queries only"
5. 输入指令：
   ```
   将 work item 7c63e4ec-6311-495d-b5b9-07de2ef2a21e 的状态改为 42fa6103-d432-4596-9c7e-d5e8bb238f54
   ```
6. **不要点击 Confirm**

---

## 7. Phase 9.3.8A-3R3 修复记录（2026-06-02）

Phase 9.3.8A-3R3 修复了 MCP routing 问题，详见 [`PHASE_9_3_8A_3R3_MCP_PROPOSED_ACTION_ROUTING_REPORT.md`](./PHASE_9_3_8A_3R3_MCP_PROPOSED_ACTION_ROUTING_REPORT.md)。

**修复**：

- Root cause：intent parser 只支持英文关键词
- 添加中文关键词（状态改为、改为等）
- API 已重建并重启
