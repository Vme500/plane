# 第 7 阶段报告：MCP Tool Preview UI

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：实现完成，py_compile/typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                       |
| ---------- | -------------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`                   |
| 基于       | `a6415b57e9` — `fix: sanitize MCP stdio adapter results` |
| 工作区状态 | 干净（无未提交修改）                                     |

---

## 2. 修改了哪些文件

| 文件                                                             | 变更                                               |
| ---------------------------------------------------------------- | -------------------------------------------------- |
| `apps/api/plane/ai/mcp_runtime.py`                               | 新增 `build_mcp_preview()` — 构建结构化 MCP 预览   |
| `apps/api/plane/app/views/external/base.py`                      | MCP 响应新增 `mcp_preview` 字段，移除 `mcp_result` |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | 新增 MCP Tool Preview UI 组件                      |

---

## 3. MCP response 结构

### 后端返回格式

```json
{
  "response": "formatted text",
  "response_html": "formatted html",
  "mode": "mcp",
  "mcp_preview": {
    "mode": "mcp",
    "adapter": "mock | stdio",
    "tool": {
      "name": "list_projects",
      "status": "success | blocked | error",
      "readonly": true
    },
    "summary": "5 project(s)",
    "items": [
      {
        "type": "project",
        "title": "My Project",
        "subtitle": "MP",
        "metadata": { "id": "uuid" }
      }
    ],
    "safety": {
      "raw_result_returned": false,
      "write_operation": false,
      "permission_filtered": true
    }
  }
}
```

### 不再返回

- ~~`mcp_result`~~ — 包含完整 execute_mcp_request 返回，可能有内部细节

---

## 4. 前端如何展示 tool preview

MCP Tool Preview 区块包含：

1. **工具名**：`[MCP] list_projects`
2. **状态标签**：success（绿色）/ blocked（黄色）/ error（红色）
3. **adapter 标签**：mock / stdio
4. **摘要**：`5 project(s)`
5. **items 列表**：最多显示 8 个 item，每个显示 title + subtitle
6. **安全提示**：`Read-only | Permission filtered`

---

## 5. 是否展示 raw JSON

**否。** `mcp_result` 已从响应中移除，`mcp_preview` 只包含结构化安全数据。

---

## 6. 是否展示 secret

**否。** 不展示 token、API key、cookie、password、stack trace、env。

---

## 7. mock adapter 是否保留

**是。** 默认使用。

---

## 8. stdio adapter 是否保留

**是。** `AI_MCP_ADAPTER=stdio` 时启用。

---

## 9. stdio allowed tools

`get_me`、`list_projects`、`retrieve_project`。

---

## 10. stdio blocked tools

`list_work_items`、`search_work_items`、`retrieve_work_item`、`list_states`、`list_labels`、`list_cycles`、`list_modules`。

---

## 11. 写操作是否仍硬拒绝

**是。**

---

## 12. 是否新增 migration

**否。**

---

## 13. 是否修改 Docker

**否。**

---

## 14. py_compile 结果

| 文件                                        | 结果    |
| ------------------------------------------- | ------- |
| `apps/api/plane/ai/mcp_runtime.py`          | ✅ 通过 |
| `apps/api/plane/ai/mcp_tools.py`            | ✅ 通过 |
| `apps/api/plane/ai/mcp_stdio_adapter.py`    | ✅ 通过 |
| `apps/api/plane/app/views/external/base.py` | ✅ 通过 |

---

## 15. typecheck/lint 结果

| 检查      | 结果    | 备注                   |
| --------- | ------- | ---------------------- |
| typecheck | ✅ 通过 | exit 0                 |
| lint      | ✅ 通过 | 0 errors, 998 warnings |

---

## 16. 已知问题

| 问题                | 说明                                           |
| ------------------- | ---------------------------------------------- |
| UI 简单             | 当前使用基础 HTML 元素，未使用 Plane UI 组件库 |
| items 无交互        | 点击 item 不会跳转到对应 project/work item     |
| 无 loading 状态区分 | MCP 工具调用期间无独立 loading indicator       |

---

## 17. 下一阶段建议

- Phase 7.1：MCP Tool Preview UI 美化（使用 Plane UI 组件）
- Phase 7.2：items 交互（点击跳转到 project/work item）
- Phase 8：审计日志
- Phase 9：写操作确认机制

---

## 18. Phase 7.5 验证记录（2026-05-28）

Phase 7.5 验证了 MCP Tool Preview API contract 和安全性，详见 [`PHASE_7_5_MCP_TOOL_PREVIEW_VALIDATION_REPORT.md`](./PHASE_7_5_MCP_TOOL_PREVIEW_VALIDATION_REPORT.md)。

**验证结果**：

- ✅ mcp_preview contract 稳定
- ✅ mcp_result 已移除
- ✅ 不展示 raw JSON / secret
- ✅ 无需代码修复
