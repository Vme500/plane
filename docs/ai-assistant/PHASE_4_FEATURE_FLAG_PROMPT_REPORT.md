# 第 4 阶段报告：AI Assistant Feature Flag + Prompt Enhancement

> 日期：2026-05-28
> 分支：feat/ai-phase-4-feature-flag-prompt
> 状态：实现完成，typecheck/lint 通过

---

## 1. 修改文件清单

### 后端（feature flags）

| 文件                                                     | 变更                                                                  |
| -------------------------------------------------------- | --------------------------------------------------------------------- |
| `packages/types/src/instance/base.ts`                    | IInstanceConfig 添加 `enable_ai_assistant` 和 `enable_ai_mcp_runtime` |
| `packages/types/src/instance/ai.ts`                      | TInstanceAIConfigurationKeys 添加两个 key                             |
| `apps/api/plane/license/api/views/instance.py`           | `/api/instances/` 返回两个新字段                                      |
| `apps/api/plane/utils/instance_config_variables/core.py` | llm_config_variables 添加两个变量                                     |

### 前端（pi-chat 页面增强）

| 文件                                                             | 变更                                                       |
| ---------------------------------------------------------------- | ---------------------------------------------------------- |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | feature flag gating + response 优化 + conversation history |

### 未修改

| 文件         | 原因                                                         |
| ------------ | ------------------------------------------------------------ |
| sidebar 组件 | `SidebarUserMenu` 中 pi-chat 是死代码，当前 sidebar 不渲染它 |
| Docker 配置  | 不在本阶段范围                                               |
| 数据库       | 不需要新 migration                                           |

---

## 2. 新增 instance config 字段

| 字段                    | 类型    | 默认值 | 来源                             |
| ----------------------- | ------- | ------ | -------------------------------- |
| `enable_ai_assistant`   | boolean | false  | `ENABLE_AI_ASSISTANT` 环境变量   |
| `enable_ai_mcp_runtime` | boolean | false  | `ENABLE_AI_MCP_RUNTIME` 环境变量 |

---

## 3. 后端如何读取 feature flag

```python
# apps/api/plane/license/api/views/instance.py
data["enable_ai_assistant"] = os.environ.get("ENABLE_AI_ASSISTANT", "0").lower() in ("1", "true")
data["enable_ai_mcp_runtime"] = os.environ.get("ENABLE_AI_MCP_RUNTIME", "0").lower() in ("1", "true")
```

识别 "1"、"true"、"True"、"TRUE" 为 true，其余为 false。

---

## 4. pi-chat 页面 gating 逻辑

| enable_ai_assistant | has_llm_configured | 页面状态                        |
| ------------------- | ------------------ | ------------------------------- |
| false               | false              | 显示 "AI Assistant is disabled" |
| false               | true               | 显示 "AI Assistant is disabled" |
| true                | false              | 显示 "LLM is not configured"    |
| true                | true               | 显示聊天界面                    |

---

## 5. sidebar entry 是否实现 gating

**否。** `SidebarUserMenu` 中的 pi-chat 入口在当前 sidebar 机制中是死代码。当前 sidebar 使用 `WORKSPACE_SIDEBAR_STATIC_NAVIGATION_ITEMS` 和 `WORKSPACE_SIDEBAR_DYNAMIC_NAVIGATION_ITEMS_LINKS`，不包含 pi-chat。跳过 sidebar gating。

---

## 6. response 展示如何优化

移除了 `JSON.stringify(res)` 兜底，改为 `extractAIResponse()` 函数：

```ts
function extractAIResponse(res: unknown): string {
  // 优先读取 response_html > response > message > result > text > content
  // 如果无法识别，返回 "No response content returned."
  // 不展示内部数据结构
}
```

---

## 7. 是否实现内存 conversation history

**是。** 使用 `ChatMessage` 类型：

```ts
type ChatMessage = {
  id: string; // 稳定 ID，不用 index
  role: "user" | "assistant";
  content: string;
  createdAt: string;
};
```

- 用户发送后添加 user message
- AI 返回后添加 assistant message
- 失败时添加 error assistant message
- 使用 `msg.id` 作为 React key（修复 no-array-index-key warning）
- 不保存到后端，页面刷新后丢失

---

## 8. 是否修复 no-array-index-key

**是。** 使用 `msg.id` 替代 `idx` 作为 React key。lint warning 从 998 降至 997。

---

## 9. 是否接 MCP

**否。**

---

## 10. 是否新增数据库 migration

**否。**

---

## 11. 是否修改 Docker

**否。**

---

## 12. typecheck/lint 结果

| 检查      | 结果                               |
| --------- | ---------------------------------- |
| typecheck | **通过**（exit 0）                 |
| lint      | **通过**（0 errors，997 warnings） |

---

## 13. 已知问题

1. `enable_ai_mcp_runtime` 已添加到类型和后端，但前端未使用（Phase 6 接 MCP 时启用）。
2. sidebar 入口未 gating（死代码，不影响功能）。
3. conversation history 仅在内存中，页面刷新后丢失（设计如此）。

---

## 14. Phase 5 建议

**Phase 5: AI Settings Page**

目标：

1. 在 Workspace Settings 中添加 "AI Assistant" 设置页
2. 管理员可以启用/禁用 AI Assistant
3. 管理员可以查看 LLM 配置状态（只读，不暴露 key）
4. 可选：管理员可以切换 AI provider/model

关键文件：

- `apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/` — 添加 AI settings 路由
- `apps/api/plane/license/api/views/instance.py` — 可能需要扩展 settings API
