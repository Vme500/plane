# 第 9.3.8A-3R 阶段报告：Web UI Proposed Action Failure Diagnosis

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：Root cause 找到并修复

---

## 1. 当前分支和 commit

| 项目        | 值                                                        |
| ----------- | --------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                    |
| 最新 commit | `2ff081941a` — `fix: validate isolated AI dev CSRF login` |
| 工作区状态  | 有未提交修复                                              |

---

## 2. 用户问题

pi-chat 输入 UUID 指令后显示 "Error: Something went wrong please try again later"，未出现 confirmation card。

---

## 3. Root Cause

**`create_ai_audit_event()` 调用使用了错误的参数名 `user_id=`，应为 `actor_id=`。**

```
TypeError: create_ai_audit_event() got an unexpected keyword argument 'user_id'
```

位于 `apps/api/plane/app/views/external/base.py:272`。

这导致 standard mode 请求路径抛出 500，前端显示 generic error。

---

## 4. 修复

将 `user_id=user_id` 改为 `actor_id=user_id`（2 处）。

---

## 5. 修复前后对比

| 检查项                | 修复前                 | 修复后             |
| --------------------- | ---------------------- | ------------------ |
| `/ai-assistant/` POST | 500 (TypeError)        | 应返回 200         |
| `ai.write.proposed`   | 1（Django shell 测试） | 应通过 Web UI 生成 |

---

## 6. 修改文件清单

| 文件                                        | 变更                                  |
| ------------------------------------------- | ------------------------------------- |
| `apps/api/plane/app/views/external/base.py` | 修复 `user_id=` → `actor_id=`（2 处） |

---

## 7. 是否可以进入 Phase 9.3.8A-3

**是。** API 已重启，用户可重试 pi-chat 指令。
