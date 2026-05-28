# 第 5 阶段报告：Workspace Settings AI Assistant 只读页面

> 日期：2026-05-28
> 分支：feat/ai-phase-5-ai-settings-page
> 状态：实现完成，typecheck/lint 通过

---

## 1. 当前分支和 commit

| 项目       | 值                                                 |
| ---------- | -------------------------------------------------- |
| 分支       | `feat/ai-phase-5-ai-settings-page`                 |
| 基于       | `feat/ai-phase-4-feature-flag-prompt` (2135df5042) |
| 工作区状态 | 干净（无未提交修改）                               |

---

## 2. 修改文件清单

| 文件                                                                                         | 变更                                                                   |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `packages/types/src/settings.ts`                                                             | `TWorkspaceSettingsTabs` 添加 `"ai-assistant"`                         |
| `packages/constants/src/settings/workspace.ts`                                               | `WORKSPACE_SETTINGS` 和 `GROUPED_WORKSPACE_SETTINGS` 添加 ai-assistant |
| `apps/web/core/components/settings/workspace/sidebar/item-icon.tsx`                          | 添加 `Bot` 图标映射                                                    |
| `packages/i18n/locales/en/workspace-settings.json`                                           | 添加 `ai_assistant` i18n key                                           |
| `apps/web/app/routes/core.ts`                                                                | 添加 `:workspaceSlug/settings/ai-assistant` 路由                       |
| `apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/ai-assistant/header.tsx` | 新增 header 组件                                                       |
| `apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/ai-assistant/page.tsx`   | 新增页面组件                                                           |

---

## 3. 新增 Workspace Settings 路径

| 项目     | 值                                                                                         |
| -------- | ------------------------------------------------------------------------------------------ |
| 路径     | `/:workspaceSlug/settings/ai-assistant`                                                    |
| 路由定义 | `apps/web/app/routes/core.ts`                                                              |
| 页面组件 | `apps/web/app/(all)/[workspaceSlug]/(settings)/settings/(workspace)/ai-assistant/page.tsx` |

---

## 4. 菜单项位置

| 项目     | 值                                               |
| -------- | ------------------------------------------------ |
| 分类     | `WORKSPACE_SETTINGS_CATEGORY.FEATURES`           |
| 标签     | `workspace_settings.settings.ai_assistant.title` |
| 图标     | `Bot` (lucide-react)                             |
| 访问权限 | `ADMIN, MEMBER`                                  |

---

## 5. 页面展示状态

| 状态卡片          | 数据来源                       | 显示                            |
| ----------------- | ------------------------------ | ------------------------------- |
| AI Assistant      | `config.enable_ai_assistant`   | Enabled / Disabled              |
| MCP Runtime       | `config.enable_ai_mcp_runtime` | Enabled / Disabled              |
| LLM Configuration | `config.has_llm_configured`    | Configured / Not configured     |
| Security note     | 静态文本                       | API keys 不展示、只读、环境变量 |

---

## 6. 是否展示 secret

**否。** 页面不展示任何 API key、token、cookie、password。

---

## 7. 是否有保存能力

**否。** 页面纯只读，无表单、无保存按钮。

---

## 8. 是否新增后端 API

**否。** 使用 Phase 4 已有的 `/api/instances/` 返回的 config 字段。

---

## 9. 是否新增 migration

**否。**

---

## 10. 是否修改 Docker

**否。**

---

## 11. 是否接 MCP

**否。**

---

## 12. typecheck/lint 结果

| 检查      | 结果                               |
| --------- | ---------------------------------- |
| typecheck | **通过**（exit 0）                 |
| lint      | **通过**（0 errors，997 warnings） |

---

## 13. 已知问题

1. **权限**：当前页面对 ADMIN 和 MEMBER 都可见（只读）。如果需要 admin-only 写权限，后续 Phase 处理。
2. **i18n**：只添加了英文 locale，未修改其他 18 种语言文件。
3. **样式**：使用内联样式（bg-green-100, bg-gray-100 等），未使用 Plane design token。

---

## 14. Phase 5.5 / Phase 6 建议

### Phase 5.5: Settings Page Enhancement

- 添加 admin-only 权限控制（如果需要）
- 使用 Plane design token 替换内联样式
- 添加更多 i18n 支持

### Phase 6: MCP Runtime (Read-Only)

- 添加 MCP client 到后端
- 扩展 endpoint 支持 `mode=mcp`
- 只读工具：list_projects, list_work_items, search_work_items 等
- 工具调用结果在聊天中结构化展示
