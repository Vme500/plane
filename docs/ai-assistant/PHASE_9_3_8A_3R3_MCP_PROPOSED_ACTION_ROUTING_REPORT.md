# 第 9.3.8A-3R3 阶段报告：MCP Proposed Action Routing Fix

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：修复完成，Django shell 验证通过

---

## 1. 当前分支和 commit

| 项目        | 值                                                                               |
| ----------- | -------------------------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                                           |
| 最新 commit | `705059faaf` — `docs: diagnose AI state update confirmation card internal error` |
| 工作区状态  | 有未提交修复                                                                     |

---

## 2. 用户问题

MCP mode 输入中文 UUID 指令后返回 "Could not determine which MCP tool to call"。

---

## 3. Root Cause

**Intent parser 只支持英文关键词。** 中文 prompt "将...状态改为..." 不匹配 `"change state"`, `"update status"` 等英文关键词。

---

## 4. 修复

在 intent parser 中添加中文关键词支持：

- `状态改为`
- `状态更改为`
- `改为`
- `状态设为`

---

## 5. Django shell 验证结果

```
success: True
proposed_action exists: True
action_type: update_work_item_state
execution_enabled: True
confirmation_token exists: True
```

---

## 6. 修改文件清单

| 文件                               | 变更                                    |
| ---------------------------------- | --------------------------------------- |
| `apps/api/plane/ai/mcp_runtime.py` | 添加中文关键词到 write intent detection |

---

## 7. 用户验证步骤

1. 打开 http://localhost:18181/ai-test/pi-chat
2. 确认已切换到 **"MCP Read-only"** 模式
3. 输入：
   ```
   将 work item 7c63e4ec-6311-495d-b5b9-07de2ef2a21e 的状态改为 42fa6103-d432-4596-9c7e-d5e8bb238f54
   ```
4. 观察 confirmation card
5. **不要点击 Confirm**

---

## 8. Phase 9.3.8A-3R4 记录（2026-06-02）

Phase 9.3.8A-3R4 记录了 confirmation card 成功并修复了 Confirm button 缺失，详见 [`PHASE_9_3_8A_3R4_CONFIRMATION_CARD_NO_CONFIRM_REPORT.md`](./PHASE_9_3_8A_3R4_CONFIRMATION_CARD_NO_CONFIRM_REPORT.md)。

**结果**：

- ✅ Confirmation card 成功显示
- ✅ Web 容器已重建（Confirm button 代码已包含）
