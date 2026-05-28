# 第 3.5 阶段报告：pi-chat 页面代码审查与本地验证

> 日期：2026-05-28
> 分支：feat/ai-phase-3-pi-chat-page
> HEAD: 59c89c635f — feat: add minimal pi-chat page

---

## 1. 当前分支和 HEAD commit

- **分支**：`feat/ai-phase-3-pi-chat-page`
- **HEAD**：`59c89c635f` — `feat: add minimal pi-chat page`
- **工作区**：干净（无未提交文件）

---

## 2. 第 3 阶段代码审查结果

### 2.1 路由（core.ts）

| 检查项 | 结果 |
|--------|------|
| 路由层级 | ✅ 正确。在 `(projects)` layout 下，与 stickies、workspace-views 同级 |
| URL 模式 | ✅ `:workspaceSlug/pi-chat`，与侧边栏 href `/${workspaceSlug}/pi-chat/` 一致 |
| 是否误伤其他路由 | ✅ 不会。路由定义独立，不影响其他 workspace/project 路由 |
| 是否符合 React Router 风格 | ✅ 使用 `layout()` + `route()` 模式，与 stickies 完全一致 |

### 2.2 页面目录位置

| 检查项 | 结果 |
|--------|------|
| 放在 `(projects)` 下 | ⚠️ 可接受，但有注意事项 |
| 是否继承项目 layout | 是。`(projects)/layout.tsx` 会渲染 `ProjectAppSidebar` 和 `ExtendedProjectSidebar` |
| 是否仍是 workspace-level 页面 | 是。URL 是 `/:workspaceSlug/pi-chat`，不依赖 projectId |
| 影响 | pi-chat 页面会显示项目侧边栏（项目列表、收藏、团队）。不影响功能，但 UI 上不是纯粹的 workspace-level 页面 |

**分析**：Plane 中所有 workspace-level 页面（stickies、drafts、notifications、analytics）都在 `(projects)` 下。这是项目的统一模式，不是我们的设计缺陷。pi-chat 保持一致是正确的。

**是否需要调整**：不需要。保持现状。

### 2.3 page.tsx 审查

| 检查项 | 结果 |
|--------|------|
| hooks 使用 | ✅ `useParams()`、`useInstance()` 符合 Plane 代码风格 |
| workspaceSlug 获取 | ✅ `const { workspaceSlug } = useParams()` + `.toString()` |
| has_llm_configured | ✅ `config?.has_llm_configured ?? false`，类型正确（IInstanceConfig.has_llm_configured: boolean） |
| AIService 实例化 | ✅ 模块级 `const aiService = new AIService()`，与 GptAssistantPopover 一致 |
| createGptTask payload | ✅ `{ prompt, task: "chat" }`，后端期望 `task`（必填）和 `prompt`（可选） |
| 后端响应格式 | ✅ 后端返回 `{ response, response_html }`，代码优先取 `response_html` |
| 错误处理 | ✅ 不泄露敏感信息。err 为 undefined 时（网络错误）显示通用消息 |
| loading 状态 | ✅ `isLoading` 控制按钮 disabled 和 "Generating response..." 提示 |
| response 展示 | ✅ 兼容多种返回格式：`response_html || response || message || JSON.stringify` |

**细微观察**（非阻塞）：
- `JSON.stringify(res)` 作为最后兜底，可能暴露内部数据结构。但仅在 API 返回异常格式时触发，Phase 3 可接受。
- `err` 在网络错误时为 `undefined`，`err?.data?.error` 安全返回 `undefined`，正确降级到通用错误消息。

### 2.4 header.tsx / layout.tsx 审查

| 检查项 | 结果 |
|--------|------|
| AppHeader / ContentWrapper | ✅ 与 stickies 完全一致的模式 |
| Breadcrumbs | ✅ 使用 `BreadcrumbLink` + `PiChatLogo` |
| import 路径 | ✅ `@plane/propel/icons`、`@plane/ui`、`@/components/common/breadcrumb-link` 均正确 |
| sidebar active state | ⚠️ 未测试。侧边栏 active 状态依赖 CSS 类匹配，需在浏览器中验证 |
| PiChatLogo | ✅ 已注册在 `packages/propel/src/icons/registry.ts` |

### 2.5 useWorkspacePaths

| 检查项 | 结果 |
|--------|------|
| isAiPath 检测 | ✅ `pathname.includes(\`/\${workspaceSlug}/pi-chat\`)` 能识别 pi-chat 路径 |
| isProjectsPath 排除 | ✅ `isProjectsPath` 已排除 `isAiPath`，不会误判 |
| 是否需要改动 | 不需要 |

---

## 3. 路由位置是否正确

**正确。** 路由在 `(projects)` layout 内，与 stickies、workspace-views 等 workspace-level 页面同级。URL 为 `/:workspaceSlug/pi-chat`，符合侧边栏 href 定义。

---

## 4. 页面目录放在 (projects) 下是否有风险

**低风险。** 这是 Plane 所有 workspace-level 页面的统一模式。pi-chat 页面会显示项目侧边栏，但这不影响功能。如需在后续阶段隐藏侧边栏，可参考 `_sidebar.tsx` 中 `isNotificationsPath` 的处理方式。

---

## 5. Node / pnpm 环境状态

| 工具 | 状态 | 项目要求 |
|------|------|----------|
| Node.js | ❌ 未安装 | >= 22.18.0 |
| pnpm | ❌ 未安装 | 10.32.1 |
| corepack | ❌ 未安装 | - |

**推荐安装方案**（需用户确认）：
```bash
# 方案 A：通过 nvm 安装
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
nvm install 22
nvm use 22
corepack enable
corepack prepare pnpm@10.32.1 --activate

# 方案 B：通过 fnm 安装
curl -fsSL https://fnm.vercel.app/install | bash
fnm install 22
fnm use 22
corepack enable
corepack prepare pnpm@10.32.1 --activate
```

---

## 6. 是否执行了 typecheck / lint

**否。** Node/pnpm 未安装，无法执行 `pnpm check:types` 或 `pnpm check:lint`。

---

## 7. 未执行原因

Node.js >= 22.18.0 和 pnpm@10.32.1 均未安装。项目使用 corepack 管理 pnpm 版本，需要先安装 Node.js。

---

## 8. 最小修复建议

**无阻塞性问题。** 代码审查未发现需要立即修复的问题。

**非阻塞观察**（可在 Phase 4 中处理）：
1. `JSON.stringify(res)` 兜底可能暴露内部数据结构，可改为更友好的默认消息。
2. 侧边栏 active 状态需在浏览器中验证。

---

## 9. 是否做了小修复

**否。** 代码审查通过，无需修复。

---

## 10. 是否仍未改后端

**是。**

---

## 11. 是否仍未改 Docker

**是。**

---

## 12. 是否仍未接 MCP

**是。**

---

## 13. 是否仍未 push

**是。**

---

## 14. 第 4 阶段是否可以开始

**可以。** 代码审查通过，无阻塞问题。第 4 阶段可以开始，建议先安装 Node/pnpm 运行 typecheck 验证，然后再进行功能增强。
