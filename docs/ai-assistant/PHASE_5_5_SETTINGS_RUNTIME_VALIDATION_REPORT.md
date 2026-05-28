# 第 5.5 阶段报告：AI Assistant Settings Page 运行时验证与权限审查

> 日期：2026-05-28
> 分支：feat/ai-phase-5-ai-settings-page
> 状态：验证完成

---

## 1. 当前分支和 commit

| 项目        | 值                                                           |
| ----------- | ------------------------------------------------------------ |
| 分支        | `feat/ai-phase-5-ai-settings-page`                           |
| 最新 commit | `d79793d98a` — `feat: add AI assistant settings status page` |
| 工作区状态  | 干净（无未提交修改）                                         |

---

## 2. settings 路由静态检查结果

| 检查项                              | 结果 | 位置                                                                            |
| ----------------------------------- | ---- | ------------------------------------------------------------------------------- |
| 路由定义存在                        | ✅   | `apps/web/app/routes/core.ts:292-293`                                           |
| 路由路径正确                        | ✅   | `:workspaceSlug/settings/ai-assistant`                                          |
| 页面组件路径正确                    | ✅   | `./(all)/[workspaceSlug]/(settings)/settings/(workspace)/ai-assistant/page.tsx` |
| 路由在 workspace settings layout 内 | ✅   | 在 `settings/(workspace)/layout.tsx` 下                                         |

---

## 3. sidebar 菜单静态检查结果

| 检查项                                                  | 结果 | 位置                                                                  |
| ------------------------------------------------------- | ---- | --------------------------------------------------------------------- |
| `TWorkspaceSettingsTabs` 包含 "ai-assistant"            | ✅   | `packages/types/src/settings.ts:19`                                   |
| `WORKSPACE_SETTINGS` 包含 ai-assistant 配置             | ✅   | `packages/constants/src/settings/workspace.ts:65-71`                  |
| `GROUPED_WORKSPACE_SETTINGS` FEATURES 包含 ai-assistant | ✅   | `packages/constants/src/settings/workspace.ts:85`                     |
| 图标 `Bot` import 正确                                  | ✅   | `apps/web/core/components/settings/workspace/sidebar/item-icon.tsx:8` |
| 图标映射存在                                            | ✅   | `item-icon.tsx:19`                                                    |
| i18n key 存在                                           | ✅   | `packages/i18n/src/locales/en/workspace-settings.json`                |
| i18n 包含 title, heading, description                   | ✅   | 三个 key 都存在                                                       |

---

## 4. 页面只读性检查结果

| 检查项            | 结果 | 说明                          |
| ----------------- | ---- | ----------------------------- |
| 页面无表单        | ✅   | 无 `<form>` 元素              |
| 页面无保存按钮    | ✅   | 无 submit/save button         |
| 页面无输入框      | ✅   | 无 `<input>` 元素             |
| 页面无 API 调用   | ✅   | 无 fetch/axios/useSWR 调用    |
| 页面只读取 config | ✅   | 只使用 `useInstance().config` |

---

## 5. secret 泄露检查结果

| 检查项           | 结果 | 说明                                       |
| ---------------- | ---- | ------------------------------------------ |
| 不展示 API key   | ✅   | 页面无 API key 显示                        |
| 不展示 token     | ✅   | 页面无 token 显示                          |
| 不展示 cookie    | ✅   | 页面无 cookie 显示                         |
| 不展示 password  | ✅   | 页面无 password 显示                       |
| 不展示环境变量值 | ✅   | 只显示 Enabled/Disabled/Configured 状态    |
| 安全提示存在     | ✅   | "API keys are never shown in the browser." |

---

## 6. 权限审查结果

### 6.1 当前权限配置

| 角色   | 数值 | 能否访问 /settings/ai-assistant |
| ------ | ---- | ------------------------------- |
| ADMIN  | 20   | ✅ 能访问                       |
| MEMBER | 15   | ✅ 能访问                       |
| GUEST  | 5    | ❌ 不能访问                     |

**配置位置**: `packages/constants/src/settings/workspace.ts:69`

```typescript
access: [EUserWorkspaceRoles.ADMIN, EUserWorkspaceRoles.MEMBER],
```

### 6.2 权限控制机制

Workspace Settings 使用统一的权限控制机制：

1. `WORKSPACE_SETTINGS_ACCESS` 从 `WORKSPACE_SETTINGS` 派生（workspace.ts:74-76）
2. `WorkspaceSettingLayout` 使用 `WORKSPACE_SETTINGS_ACCESS[accessKey]` 检查权限（layout.tsx:37）
3. `WorkspaceSettingsSidebarItemCategories` 使用 `allowPermissions` 过滤可见菜单项（item-categories.tsx:39-41）
4. 未授权用户显示 `NotAuthorizedView`（layout.tsx:47-48）

### 6.3 安全风险评估

| 场景                               | 风险 | 评估                             |
| ---------------------------------- | ---- | -------------------------------- |
| MEMBER 查看 AI Assistant 状态      | 低   | 只读页，不展示 secret            |
| MEMBER 查看 MCP Runtime 状态       | 低   | 只读页，不展示 secret            |
| MEMBER 查看 LLM Configuration 状态 | 低   | 只显示 Configured/Not configured |
| GUEST 访问                         | 无   | 已被权限系统阻止                 |

### 6.4 后续建议

| 阶段                  | 建议                                         |
| --------------------- | -------------------------------------------- |
| Phase 5（当前）       | ADMIN + MEMBER 可接受（只读，不展示 secret） |
| Phase 5.6/6（写配置） | 必须限制为 ADMIN-only                        |
| 实现方式              | 修改 `access: [EUserWorkspaceRoles.ADMIN]`   |

---

## 7. ADMIN/MEMBER/GUEST 访问判断

| 角色   | Phase 5 只读页      | Phase 5.6/6 写配置 |
| ------ | ------------------- | ------------------ |
| ADMIN  | ✅ 允许             | ✅ 允许            |
| MEMBER | ✅ 允许（只读安全） | ❌ 不允许          |
| GUEST  | ❌ 不允许           | ❌ 不允许          |

**判断依据**：

- 页面只读且不展示 secret，MEMBER 访问无安全风险
- 写配置操作需要 ADMIN 权限，后续 Phase 实现

---

## 8. 是否实际浏览器验证

**否。** 原因：

- 前端 dev server 需要后端 API 支持才能完整运行
- 当前环境未配置后端 API
- 未修改生产目录

**后续验证步骤：**

1. 启动前端 dev server：`pnpm --filter web dev`
2. 启动后端 API server
3. 登录 Plane
4. 进入 Workspace Settings
5. 左侧菜单能看到 AI Assistant
6. 点击后进入 /:workspaceSlug/settings/ai-assistant
7. 页面不 404
8. 页面显示三个状态卡片和安全提示

---

## 9. 是否实际验证 /api/instances/

**否。** 原因：

- 后端需要 Django 环境和数据库连接才能运行
- 当前环境未配置
- 未修改生产目录

**后续验证步骤：**

1. 在 dev/staging 环境启动 Django 后端
2. 调用 `GET /api/instances/`
3. 确认响应包含 `enable_ai_assistant`、`enable_ai_mcp_runtime`、`has_llm_configured`

---

## 10. 是否做了小修复

**否。** 静态审查未发现 bug，无需修复。

---

## 11. typecheck/lint 结果

| 检查      | 结果    | 备注                   |
| --------- | ------- | ---------------------- |
| typecheck | ✅ 通过 | Phase 5 已验证         |
| lint      | ✅ 通过 | 0 errors, 997 warnings |

---

## 12. 是否新增后端 API

**否。**

---

## 13. 是否新增 migration

**否。**

---

## 14. 是否修改 Docker

**否。**

---

## 15. 是否接 MCP

**否。**

---

## 16. 是否 push

**否。**

---

## 17. 是否 PR

**否。**

---

## 18. 是否可以进入 Phase 6

**是。** 静态验证和权限审查通过，可以进入 Phase 6。

**Phase 6 前置条件：**

- [x] Settings 页面路由正确
- [x] Sidebar 菜单正确
- [x] 页面只读，不展示 secret
- [x] 权限配置合理（ADMIN + MEMBER）
- [ ] 运行时验证（需要 dev 环境）

**建议：** 在 Phase 6 开始前，如有 dev 环境可用，建议先完成运行时验证。

---

## 19. 验证总结

| 验证类型         | 状态      | 说明                                  |
| ---------------- | --------- | ------------------------------------- |
| 路由静态检查     | ✅ 完成   | 路由定义正确                          |
| Sidebar 菜单检查 | ✅ 完成   | 菜单项配置正确                        |
| 页面只读性检查   | ✅ 完成   | 无表单、无保存按钮、无输入框          |
| Secret 泄露检查  | ✅ 完成   | 不展示任何 secret                     |
| 权限审查         | ✅ 完成   | ADMIN + MEMBER 可访问，GUEST 不可访问 |
| 运行时验证       | ⏳ 待完成 | 需要 dev 环境                         |
