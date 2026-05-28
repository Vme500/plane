# 第 3 阶段报告：pi-chat Minimal Page Skeleton

> 日期：2026-05-28
> 分支：feat/ai-phase-3-pi-chat-page
> 状态：实现完成，待人工验证

---

## 1. 修改文件清单

### 新增文件

| 文件 | 用途 |
|------|------|
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` | pi-chat 聊天页面组件 |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/layout.tsx` | 页面布局（Header + ContentWrapper） |
| `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/header.tsx` | 页面 Header（Breadcrumbs + PiChatLogo） |

### 修改文件

| 文件 | 变更 |
|------|------|
| `apps/web/app/routes/core.ts` | 添加 pi-chat 路由（3 行） |

### 未修改

| 文件 | 原因 |
|------|------|
| 后端代码 | 不需要，复用现有 `/ai-assistant/` endpoint |
| Docker 配置 | 不在本阶段范围 |
| 数据库 | 不需要新 migration |
| i18n 文件 | 使用英文硬编码，复用已有 `pi_chat` key |
| 侧边栏组件 | `pi-chat` 入口已存在，无需修改 |

---

## 2. 新增路由

```
/:workspaceSlug/pi-chat
```

路由定义在 `apps/web/app/routes/core.ts`，位于 `(projects)` layout 下，与 stickies、drafts 等同级。

---

## 3. 页面组件路径

```
apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/
├── page.tsx      # 主页面：聊天输入框 + 消息展示 + LLM 配置检查
├── layout.tsx    # 布局：AppHeader + ContentWrapper + Outlet
└── header.tsx    # Header：Breadcrumbs + PiChatLogo
```

---

## 4. 是否调用现有 AIService

**是。** 使用 `apps/web/core/services/ai.service.ts` 中的 `createGptTask()` 方法。

调用方式：
```ts
aiService.createGptTask(workspaceSlug, { prompt: userInput, task: "chat" })
```

返回值处理（兼容多种格式）：
```ts
const responseText = res?.response_html || res?.response || res?.message || JSON.stringify(res);
```

---

## 5. 是否接入 MCP

**否。** 第 3 阶段仅做简单 prompt-response，不接入 MCP runtime。

---

## 6. 是否新增数据库 migration

**否。**

---

## 7. 是否修改 Docker

**否。**

---

## 8. 如何本地验证

### 前提条件
1. Plane 开发环境已配置（pnpm install 完成）
2. `LLM_API_KEY` 环境变量已设置

### 验证步骤

1. 启动 web 开发服务器：
   ```bash
   cd apps/web
   pnpm dev
   ```

2. 访问 `http://localhost:3000/{workspaceSlug}/pi-chat`

3. 验证场景：

| 场景 | 预期行为 |
|------|----------|
| `LLM_API_KEY` 未设置 | 显示黄色提示："LLM is not configured..." |
| `LLM_API_KEY` 已设置 | 显示聊天输入框和空消息区 |
| 输入问题并点击 Send | 显示用户消息，然后显示 AI 回复 |
| 网络错误 | 显示错误提示 |
| Enter 键 | 发送消息（等同点击 Send） |

---

## 9. 已知问题

1. **feature flag 未完整实现**：页面始终可访问，未用 `enable_ai_assistant` 控制。TODO 注释已添加，Phase 4 实现。
2. **无 conversation history**：页面刷新后历史丢失，设计如此（Phase 3 最小范围）。
3. **无 streaming**：请求为同步 POST，等待完整响应。
4. **返回值格式不确定**：`createGptTask()` 返回结构可能因 provider 不同而异，已做兼容处理。
5. **未运行 lint/type check**：pnpm 未安装，需人工在开发环境中验证编译。
6. **无 i18n**：使用英文硬编码文案。

---

## 10. 第 4 阶段建议

**Phase 4: Basic Prompt-Response via Existing Endpoint**

目标：
1. 验证 `createGptTask()` 返回值格式，优化响应展示
2. 添加 `enable_ai_assistant` feature flag 控制页面访问
3. 添加基本的 conversation history（内存中）
4. 改进错误处理和 loading 状态
5. 可选：添加 i18n 支持

关键文件：
- `apps/web/app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx` — 页面逻辑
- `apps/api/plane/license/api/views/instance.py` — 添加 `enable_ai_assistant` 字段
- `packages/types/src/instance/base.ts` — 添加类型定义
