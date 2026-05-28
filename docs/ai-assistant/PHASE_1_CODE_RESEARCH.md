# 第 1 阶段报告：代码调研

> 调研日期：2026-05-28
> 分支：feat/ai-phase-1-research
> 目标：了解 Plane 前后端架构，识别 AI 功能集成点，不修改功能代码。

## 0. 关键发现：Plane 已有 AI 基础设施

**这是本次调研最重要的发现。** Plane 已经有部分 AI 相关代码：

| 组件 | 路径 | 状态 |
|------|------|------|
| AI Service（共享包） | `packages/services/src/ai/ai.service.ts` | 存在，有 `prompt()` 和 `rephraseGrammar()` 方法 |
| AI Service（Web 应用） | `apps/web/core/services/ai.service.ts` | 存在，调用 `/api/workspaces/{slug}/ai-assistant/` |
| AI Editor Tasks 常量 | `apps/web/core/constants/ai.ts` | 存在，定义 `AI_EDITOR_TASKS` 枚举 |
| AI Editor 菜单 | `apps/web/ce/components/pages/editor/ai/menu.tsx` | 存在，页面编辑器内 AI 功能 |
| Pi Chat 侧边栏入口 | `apps/web/core/components/workspace/sidebar/user-menu.tsx` | 存在，`pi-chat` 菜单项 |
| LLM 配置检查 | `packages/types/src/instance/base.ts` | 存在，`has_llm_configured: boolean` |
| 废弃的 OpenAI 环境变量 | `.env.example` | 存在，`OPENAI_API_BASE`、`OPENAI_API_KEY`、`GPT_ENGINE` |

**但后端 AI 端点似乎已移除**：前端调用的 `/api/workspaces/{slug}/ai-assistant/` 和 `/api/workspaces/{slug}/rephrase-grammar/` 在当前 `apps/api/plane/app/urls/workspace.py` 中不存在。

**影响**：我们的 AI Assistant 集成可以复用或扩展现有的 `AIService` 和 `pi-chat` 入口，而不是从零开始。

---

## 1. 前端结构

### 1.1 左侧栏组件

**主入口**：`apps/web/core/components/workspace/sidebar/sidebar-menu-items.tsx`
- `SidebarMenuItems` 组件，编排静态和动态导航项

**用户菜单（Home, Your Work, Drafts, Pi Chat）**：
- `apps/web/core/components/workspace/sidebar/user-menu.tsx`
- `SIDEBAR_USER_MENU_ITEMS` 数组，包含 key：`home`, `dashboards`, `your-work`, `drafts`, `pi-chat`
- 每项有 `labelTranslationKey`、`href`、`icon`

**工作区菜单（Projects, Views, Cycles, Analytics）**：
- `apps/web/core/components/workspace/sidebar/workspace-menu.tsx`
- `SIDEBAR_WORKSPACE_MENU_ITEMS` 数组

**Stickies 入口**：
- 定义在 `packages/constants/src/workspace.ts` 的 `WORKSPACE_SIDEBAR_STATIC_NAVIGATION_ITEMS`
- key: `stickies`, href: `/stickies/`

**AI 助手入口建议**：
- 方案 A：在 `SIDEBAR_USER_MENU_ITEMS` 中添加 `ai-assistant` 项（类似 `pi-chat`）
- 方案 B：在 `WORKSPACE_SIDEBAR_STATIC_NAVIGATION_ITEMS` 中添加（类似 `stickies`）
- 推荐方案 A，因为已有 `pi-chat` 先例

### 1.2 Workspace Settings 菜单

**布局**：`apps/web/app/(all)/[workspaceSlug]/(settings)/layout.tsx`
- `WorkspaceSettingLayout`，左侧 `WorkspaceSettingsSidebarRoot`，右侧 `<Outlet />`

**侧边栏**：
- `apps/web/core/components/settings/workspace/sidebar/root.tsx` — `WorkspaceSettingsSidebarRoot`
- `apps/web/core/components/settings/workspace/sidebar/item-categories.tsx` — 遍历 `WORKSPACE_SETTINGS_CATEGORIES`

**常量**：`packages/constants/src/settings/workspace.ts`
- `WORKSPACE_SETTINGS` 定义 tabs：`general`, `members`, `billing-and-plans`, `export`, `webhooks`
- 分类：`ADMINISTRATION`, `FEATURES`, `DEVELOPER`

**AI 设置建议**：在 `DEVELOPER` 分类中添加 `ai-assistant` tab，或新建 `AI` 分类

### 1.3 个人设置菜单

**布局**：`apps/web/app/(all)/settings/profile/layout.tsx`

**侧边栏**：
- `apps/web/core/components/settings/profile/sidebar/root.tsx`
- `apps/web/core/components/settings/profile/sidebar/item-categories.tsx`
- tabs：`general`, `security`, `preferences`, `notifications`, `api-tokens`
- 分类：`YOUR_PROFILE`, `DEVELOPER`

**常量**：`packages/constants/src/settings/profile.ts`

**AI 偏好建议**：在 `YOUR_PROFILE` 分类中添加 `ai-preferences` tab

### 1.4 路由系统

**框架**：React Router（非 Next.js），客户端 SPA（`ssr: false`）

**配置**：
- `apps/web/react-router.config.ts` — `ssr: false`
- `apps/web/app/routes.ts` — 合并 `coreRoutes` 和 `extendedRoutes`
- `apps/web/app/routes/core.ts` — 所有核心路由
- `apps/web/app/routes/extended.ts` — 空数组，企业版扩展点

**路由结构**：
```
/:workspaceSlug                    — 工作区首页
/:workspaceSlug/stickies           — 便签
/:workspaceSlug/drafts             — 草稿
/:workspaceSlug/settings           — 工作区设置
/:workspaceSlug/settings/members   — 成员管理
/:workspaceSlug/settings/webhooks  — Webhook
/settings/profile/:profileTabId    — 个人设置
```

**AI 路由建议**：
- `/:workspaceSlug/pi-chat` 或 `/:workspaceSlug/ai-assistant` — AI 聊天页面
- `/:workspaceSlug/settings/ai-assistant` — AI 设置页

### 1.5 API Client 封装

**两层架构**：

1. **共享基础服务**：`packages/services/src/api.service.ts`
   - 抽象类 `APIService`，使用 axios，`withCredentials: true`
   - 提供 `get()`, `post()`, `put()`, `patch()`, `delete()` 方法

2. **Web 应用服务**：`apps/web/core/services/api.service.ts`
   - 继承 `APIService`，添加 401 拦截器（重定向到登录页）

**AI 服务**：
- `packages/services/src/ai/ai.service.ts` — `AIService` 类
- `apps/web/core/services/ai.service.ts` — Web 版 `AIService`

**Store 层（MobX）**：
- `apps/web/core/store/root.store.ts` — `CoreRootStore`，实例化所有 store
- 组件通过 `useInstance()`, `useWorkspace()` 等 hooks 访问 store
- store 内部使用 service 类调用 API

### 1.6 i18n 文案

**包**：`packages/i18n/`

**配置**：
- `packages/i18n/src/core/instance.ts` — i18next 实例，使用 `i18next-icu`
- `packages/i18n/src/hooks/use-translation.ts` — `useTranslation()` hook

**支持语言**：19 种（en, fr, es, ja, zh-CN, zh-TW, ru, it, cs, sk, de, ua, pl, ko, pt-BR, id, ro, vi-VN, tr-TR）

**命名空间**：28 个（common, settings, workspace-settings, stickies, work-item 等）

**本地化文件**：`packages/i18n/locales/{lang}/{namespace}.json`

**使用方式**：`const { t } = useTranslation();` 然后 `t("sidebar.home")`

**AI 文案建议**：在 `common` 或新建 `ai` 命名空间中添加 AI 相关翻译

### 1.7 Feature Flag 使用方式

**Plane 没有传统的 feature flag 系统**。使用以下机制：

1. **实例配置布尔值**：`packages/types/src/instance/base.ts` 的 `IInstanceConfig`
   - `enable_signup`, `is_google_enabled`, `has_llm_configured` 等
   - 通过 `/api/instances/` 获取，存入 `InstanceStore`
   - 组件通过 `useInstance()` 访问

2. **项目级 feature toggle**：`apps/web/core/components/project/settings/features-list.tsx`
   - `PROJECT_FEATURES_LIST` 定义 cycles, modules, views 等
   - 通过 `updateProject()` API 切换

3. **编译时常量**：`packages/constants/src/issue/filter.ts`
   - `ENABLE_ISSUE_DEPENDENCIES = false`

**AI Feature Flag 建议**：
- 在 `IInstanceConfig` 中添加 `enable_ai_assistant: boolean`
- 通过 `/api/instances/` 返回给前端
- 组件通过 `useInstance()` 检查

---

## 2. 后端结构

### 2.1 apps/api 目录结构

**框架**：Django + Django REST Framework (DRF)

**目录结构**（`apps/api/plane/`）：

| 目录 | 用途 |
|------|------|
| `api/` | 公开 REST API (v1)，token 认证 |
| `app/` | 内部应用 API，session 认证 |
| `authentication/` | 认证提供者（OAuth, email, magic link） |
| `bgtasks/` | Celery 后台任务 |
| `db/` | Django models, migrations, mixins |
| `license/` | 实例许可，管理配置 |
| `middleware/` | 请求日志，DB 路由，请求体大小限制 |
| `settings/` | Django 设置模块 |
| `space/` | 公开 Space API |
| `utils/` | 共享工具（权限, 分页, 过滤器） |

**URL 路由**（`apps/api/plane/urls.py`）：
- `api/` → `plane.app.urls`（内部 API，session 认证）
- `api/v1/` → `plane.api.urls`（公开 API，token 认证）
- `api/public/` → `plane.space.urls`
- `api/instances/` → `plane.license.urls`
- `auth/` → `plane.authentication.urls`

### 2.2 Workspace 权限校验

**文件**：`apps/api/plane/app/permissions/workspace.py`

**角色常量**：
- `Admin = 20`
- `Member = 15`
- `Guest = 5`

**权限类**：
- `WorkSpaceBasePermission` — POST 允许任何认证用户；SAFE_METHODS 总是允许；PUT/PATCH 需要 Admin 或 Member；DELETE 需要 Admin
- `WorkspaceEntityPermission` — SAFE_METHODS 对任何活跃工作区成员；写操作需要 Admin 或 Member
- `WorkspaceViewerPermission` — 任何活跃工作区成员
- `WorkspaceUserPermission` — 任何活跃工作区成员

**检查方式**：`WorkspaceMember.objects.filter(member=request.user, workspace__slug=view.workspace_slug, ...)`

### 2.3 Project 权限校验

**文件**：`apps/api/plane/app/permissions/project.py`

**角色**：`ROLE.ADMIN = 20`, `ROLE.MEMBER = 15`, `ROLE.GUEST = 5`

**权限类**：
- `ProjectBasePermission` — SAFE_METHODS 需要活跃工作区成员；写操作需要项目 Admin 或工作区 Admin
- `ProjectMemberPermission` — SAFE_METHODS 对任何项目成员
- `ProjectEntityPermission` — 处理 `project_identifier` 查找
- `ProjectAdminPermission` — 仅项目 Admin

**装饰器**：`apps/api/plane/app/permissions/base.py` 的 `allow_permission(allowed_roles, level, creator, model)`

### 2.4 User / Personal Access Token

**User 模型**：`apps/api/plane/db/models/user.py`
- 继承 `AbstractBaseUser` + `PermissionsMixin`
- UUID 主键，`email` 作为 `USERNAME_FIELD`
- 字段：`username`, `display_name`, `is_bot`, `bot_type` 等

**API Token 模型**：`apps/api/plane/db/models/api.py`
- `APIToken` — UUID 主键，`token` 生成为 `"plane_api_" + uuid4().hex`
- `user_type`: 0=Human, 1=Bot
- `is_service` 标志（服务 token 有更高频率限制）
- `allowed_rate_limit`（默认 "60/min"）

**认证**：`apps/api/plane/api/middleware/api_authentication.py`
- `APIKeyAuthentication` — 读取 `X-Api-Key` 头
- 查找 `APIToken`（token 匹配，is_active=True，未过期）

**频率限制**：
- `ApiKeyRateThrottle`：60/分钟
- `ServiceTokenRateThrottle`：300/分钟

### 2.5 Settings 模块

**Django 设置**：`apps/api/plane/settings/`

| 文件 | 用途 |
|------|------|
| `common.py` | 主设置：INSTALLED_APPS, MIDDLEWARE, REST_FRAMEWORK, DATABASE, REDIS, CELERY |
| `production.py` | 生产覆盖 |
| `local.py` | 本地开发覆盖 |
| `test.py` | 测试设置 |
| `redis.py` | Redis 连接单例 |
| `storage.py` | S3/MinIO 存储后端 |
| `mongo.py` | MongoDB 连接（API 活动日志） |

**工作区设置模型**（`apps/api/plane/db/models/workspace.py`）：
- `WorkspaceUserProperties` — 用户工作区过滤/显示偏好
- `WorkspaceUserPreference` — 用户侧边栏/导航 pin 偏好
- `WorkspaceHomePreference` — 用户首页小部件配置
- `WorkspaceTheme` — 自定义工作区颜色主题

### 2.6 Audit / Activity 模块

**Issue 活动跟踪**：`apps/api/plane/db/models/issue.py`
- `IssueActivity` 模型 — 跟踪每个 issue 变更：`verb`, `field`, `old_value`, `new_value`

**活动跟踪任务**：`apps/api/plane/bgtasks/issue_activities_task.py`
- 大型 Celery 任务，跟踪 name, description, priority, state, labels, assignees 等变更

**模型级审计 mixin**：`apps/api/plane/db/mixins.py`
- `TimeAuditModel` — `created_at`, `updated_at`
- `UserAuditModel` — `created_by`, `updated_by`
- `AuditModel` — 组合两者 + 软删除
- `ChangeTrackerMixin` — 跟踪字段变更

**API 请求日志**：`apps/api/plane/middleware/logger.py`
- `RequestLoggerMiddleware` — 记录每个请求
- `APITokenLogMiddleware` — 对 API token 请求记录完整详情

**API 活动日志任务**：`apps/api/plane/bgtasks/logger_task.py`
- `process_logs` Celery 任务，保存到 MongoDB 或 PostgreSQL

### 2.7 Migration 机制

**迁移目录**：`apps/api/plane/db/migrations/` — 122 个迁移文件（0001 到 0121）

**模式**：标准 Django migrations（`makemigrations` 和 `migrate`）

**软删除**：`SoftDeletionManager` 默认过滤 `deleted_at__isnull=True`，软删除触发 Celery 任务级联

### 2.8 Worker / Async Task 机制

**框架**：Celery + RabbitMQ (AMQP)

**配置**：`apps/api/plane/celery.py`
- Broker: RabbitMQ
- Beat scheduler: `django_celery_beat.schedulers.DatabaseScheduler`

**定时任务**（beat schedule）：
- `email_notification_task.stack_email_notification` — 每 5 分钟
- `tracer.instance_traces` — 每 6 小时
- `deletion_task.hard_delete` — 每天 00:00 UTC
- `issue_automation_task.archive_and_close_old_issues` — 每天 01:00 UTC
- `cleanup_task.*` — 每天 02:00-03:30 UTC（清理日志、版本等）

**后台任务文件**：`apps/api/plane/bgtasks/` — 25+ 个任务文件

---

## 3. Docker / 部署结构

### 3.1 Compose 文件

**生产**：`docker-compose.yml` — 12 个服务
- `web`, `admin`, `space` — 前端服务
- `api`, `worker`, `beat-worker`, `migrator` — 后端服务（共享同一 Dockerfile）
- `live` — 实时服务
- `plane-db` (PostgreSQL), `plane-redis` (Valkey), `plane-mq` (RabbitMQ), `plane-minio` (MinIO)
- `proxy` — Caddy 反向代理

**本地开发**：`docker-compose-local.yml`
- 仅后端服务，前端通过 `pnpm dev` 本地运行
- 使用 `Dockerfile.dev`，挂载代码卷实现热重载

### 3.2 .env.example

**可用变量**：
- 数据库：`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- Redis：`REDIS_HOST`, `REDIS_PORT`
- RabbitMQ：`RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`
- S3：`AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_ENDPOINT_URL`
- AI（废弃）：`OPENAI_API_BASE`, `OPENAI_API_KEY`, `GPT_ENGINE`
- 端口：`LISTEN_HTTP_PORT`, `LISTEN_HTTPS_PORT`

### 3.3 服务启动顺序

```
plane-db, plane-redis, plane-mq, plane-minio
    ↓
migrator（运行一次后退出）
    ↓
api（等待 db + redis）
    ↓
worker, beat-worker
    ↓
web, admin, space
    ↓
proxy
```

### 3.4 如何新增 plane-ai-agent 服务

**方案 A：独立容器（类似 `live`）**
1. 在 `apps/ai-agent/` 创建 Dockerfile
2. 在 `docker-compose.yml` 添加服务
3. 在 `apps/proxy/Caddyfile.ce` 添加路由
4. 在 `deployments/cli/community/docker-compose.yml` 添加预构建镜像

**方案 B：Sidecar（类似 `worker`）**
1. 在 `apps/api/bin/` 添加入口脚本
2. 在 `docker-compose.yml` 添加使用同一 Dockerfile 的服务

### 3.5 如何新增 plane-mcp-server sidecar

**推荐方案 B**（复用 API 镜像）：
1. 创建 `apps/api/bin/docker-entrypoint-mcp-server.sh`
2. 在 `docker-compose.yml` 添加服务：
   ```yaml
   plane-mcp-server:
     container_name: plane-mcp-server
     build:
       context: .
       dockerfile: ./apps/api/Dockerfile.api
     command: ["./bin/docker-entrypoint-mcp-server.sh"]
     restart: always
     env_file:
       - ./apps/api/.env
     depends_on:
       - api
       - plane-db
       - plane-redis
   ```

### 3.6 不应该修改的文件

1. `docker-compose.yml` — 生产 compose 定义
2. `apps/api/bin/docker-entrypoint-*.sh` — 生产入口脚本
3. `apps/proxy/Caddyfile.ce` — 生产反向代理路由
4. `apps/api/Dockerfile.api` — 生产后端 Dockerfile
5. `apps/web/Dockerfile.web` — 生产前端 Dockerfile
6. `deployments/` — 所有部署脚本
7. `.env.example` — 环境变量参考

---

## 4. 第一版推荐改动点

### 4.1 AI 助手左侧栏入口

**推荐位置**：在 `SIDEBAR_USER_MENU_ITEMS` 中添加 `ai-assistant` 项

**修改文件**：
- `apps/web/core/components/workspace/sidebar/user-menu.tsx` — 添加菜单项
- `packages/i18n/locales/en/common.json` — 添加翻译 key

**条件渲染**：通过 `instance.config?.enable_ai_assistant` 控制显示

### 4.2 Workspace Settings → AI Assistant

**推荐位置**：在 `WORKSPACE_SETTINGS` 的 `DEVELOPER` 分类中添加

**修改文件**：
- `packages/constants/src/settings/workspace.ts` — 添加 tab
- `apps/web/core/components/settings/workspace/sidebar/item-categories.tsx` — 添加图标
- 新建 `apps/web/core/components/workspace/settings/ai-assistant.tsx` — 设置页面内容

### 4.3 Personal Settings → AI Preferences

**推荐位置**：在 `PROFILE_SETTINGS` 的 `YOUR_PROFILE` 分类中添加

**修改文件**：
- `packages/constants/src/settings/profile.ts` — 添加 tab
- 新建 `apps/web/core/components/settings/profile/content/pages/ai-preferences.tsx`

### 4.4 后端 AI Settings API 初稿

**推荐位置**：在 `plane.app` 中新建 `ai` 模块

**新建文件**：
- `apps/api/plane/app/views/ai.py` — AI 设置视图
- `apps/api/plane/app/serializers/ai.py` — AI 设置序列化器
- `apps/api/plane/app/urls/ai.py` — AI URL 配置
- `apps/api/plane/db/models/ai.py` — AI 设置模型

**API 端点**：
- `GET /api/workspaces/{slug}/ai/settings/` — 获取 AI 设置
- `PUT /api/workspaces/{slug}/ai/settings/` — 更新 AI 设置
- `POST /api/workspaces/{slug}/ai/chat/` — AI 聊天

### 4.5 MCP Runtime 放置建议

**推荐位置**：在 `plane.app` 中新建 `ai` 模块，或在 `plane.bgtasks` 中添加

**新建文件**：
- `apps/api/plane/ai/` — AI 模块（MCP client, runtime, tools）
- `apps/api/plane/ai/mcp_client.py` — MCP 客户端
- `apps/api/plane/ai/runtime.py` — AI Runtime 编排
- `apps/api/plane/ai/tools.py` — 工具定义和安全检查

### 4.6 审计日志放置建议

**推荐方案**：扩展现有 `IssueActivity` 模式

**新建文件**：
- `apps/api/plane/db/models/ai.py` — `AIActivity` 模型
- `apps/api/plane/bgtasks/ai_activities_task.py` — AI 活动跟踪任务

**字段**：`user_id`, `workspace_id`, `project_id`, `tool_name`, `parameters`（脱敏）, `result_summary`, `error`, `confirmed`, `model`, `runtime`, `created_at`

---

## 5. 风险

### 5.1 上游更新冲突

**风险**：fork 后上游更新可能导致合并冲突
**缓解**：
- 保持 `main-ai` 定期 rebase 到 `upstream/preview`
- 功能改动尽量模块化，减少与上游代码的交叉
- 使用 feature flag 隔离 AI 功能

### 5.2 Secret 保存

**风险**：API key 可能意外提交到 Git
**缓解**：
- `.env` 不提交
- `.env.example` 只写占位符
- pre-commit hook 检查 secret 模式
- API key 只保存在服务端数据库

### 5.3 权限绕过

**风险**：AI 可能绕过 Plane 的权限模型
**缓解**：
- AI Runtime 使用与当前用户相同的权限
- 不使用管理员级 API token
- 复用现有的 `WorkSpaceBasePermission` 和 `ProjectBasePermission`

### 5.4 MCP 兼容性

**风险**：`plane-mcp-server` 可能与 self-hosted Plane 版本不兼容
**缓解**：
- 测试常见 self-hosted 版本
- 文档说明支持的版本
- 处理 404/权限/路径错误

### 5.5 Docker 复杂度

**风险**：新增服务增加部署复杂度
**缓解**：
- 第一版可以将 MCP client 集成在 API 服务内（不新增容器）
- 使用 feature flag 控制，不启用时不增加资源消耗
- 文档说明配置步骤

### 5.6 Claude Code Runtime 风险

**风险**：高级 runtime 可能有安全风险
**缓解**：
- 默认关闭
- 必须沙箱
- 不作为第一批官方 PR
- 仅在 fork 中提供

---

## 6. 总结

### 6.1 可复用的现有基础设施

| 组件 | 可复用性 | 说明 |
|------|----------|------|
| `AIService` | 高 | 可扩展为 AI Assistant 服务 |
| `pi-chat` 侧边栏入口 | 高 | 可作为 AI Assistant 入口 |
| `has_llm_configured` | 高 | 可扩展为 AI feature flag |
| `IssueActivity` 模式 | 高 | 可作为 AI 审计日志参考 |
| `APIToken` 模型 | 高 | 可用于 AI API 认证 |
| `WorkspaceUserPreference` | 中 | 可用于 AI 偏好设置 |
| Celery 任务 | 高 | 可用于 AI 异步处理 |

### 6.2 需要新建的组件

| 组件 | 位置 | 说明 |
|------|------|------|
| AI 设置模型 | `apps/api/plane/db/models/ai.py` | 工作区 AI 配置 |
| AI 设置 API | `apps/api/plane/app/views/ai.py` | CRUD AI 设置 |
| AI 聊天 API | `apps/api/plane/app/views/ai.py` | 聊天端点 |
| MCP Client | `apps/api/plane/ai/mcp_client.py` | MCP 协议客户端 |
| AI Runtime | `apps/api/plane/ai/runtime.py` | AI 对话编排 |
| AI 审计日志 | `apps/api/plane/db/models/ai.py` | `AIActivity` 模型 |
| AI 设置页面 | `apps/web/core/components/workspace/settings/` | 前端设置 UI |
| AI 聊天面板 | `apps/web/core/components/ai/` | 前端聊天 UI |
