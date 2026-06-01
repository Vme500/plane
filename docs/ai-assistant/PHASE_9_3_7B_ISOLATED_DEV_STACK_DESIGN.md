# 第 9.3.7B 阶段报告：Isolated Fork Dev Stack Design

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：设计完成，未启动 Docker

---

## 1. 当前分支和 commit

| 项目        | 值                                                                          |
| ----------- | --------------------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                                      |
| 最新 commit | `91fdfa90a2` — `docs: assess AI state update runtime environment readiness` |
| 工作区状态  | 干净（无未提交修改）                                                        |

---

## 2. localhost:18080 不可用于测试的原因

| 原因                      | 说明                                                                   |
| ------------------------- | ---------------------------------------------------------------------- |
| 运行官方镜像              | `makeplane/plane-backend:v1.3.1`，不含 fork 代码                       |
| 无 AI 模块                | 容器内无 `/code/plane/ai/` 目录                                        |
| 无 AIAuditEvent migration | 官方镜像不含此 model                                                   |
| 无 AI feature flags       | `enable_ai_assistant` / `enable_ai_mcp_runtime` 在官方 v1.3.1 中不存在 |
| 数据库可能含真实数据      | 不适合测试                                                             |

---

## 3. Docker/dev Stack 调研结果

| 项目             | 说明                                                                 |
| ---------------- | -------------------------------------------------------------------- |
| 官方 compose     | `docker-compose.yml`（完整 stack）                                   |
| 本地开发 compose | `docker-compose-local.yml`（redis, mq, minio）                       |
| API Dockerfile   | `apps/api/Dockerfile.api`（生产）, `apps/api/Dockerfile.dev`（开发） |
| Web Dockerfile   | `apps/web/Dockerfile.web`                                            |
| .env.example     | 存在，含 DB/Redis/RabbitMQ/MinIO 配置                                |
| 后端依赖         | PostgreSQL, Redis, RabbitMQ, MinIO                                   |
| Migration 命令   | `python manage.py migrate`                                           |

---

## 4. 独立 Dev Stack 目标

| 目标               | 说明                                           |
| ------------------ | ---------------------------------------------- |
| 从 fork 分支构建   | 使用本地代码，不依赖官方镜像                   |
| 独立数据库         | 独立 volume，不影响现有数据                    |
| 独立 Redis         | 独立 volume                                    |
| 独立端口           | 不覆盖 localhost:18080                         |
| 不复用生产 .env    | 使用独立 .env.ai-dev.local                     |
| 可应用 migration   | 包括 0122_aiauditevent                         |
| 可启用 AI flags    | ENABLE_AI_ASSISTANT=1, ENABLE_AI_MCP_RUNTIME=1 |
| 可配置 LLM         | 通过 .env.ai-dev.local（不提交）               |
| 可创建测试数据     | 一次性 workspace/project/issue                 |
| 可执行 Phase 9.3.8 | runtime test                                   |
| 可清理             | 删除 dev volume 即可                           |

---

## 5. 推荐 Compose/Project/Volume/Port 命名

| 项目             | 推荐值                          |
| ---------------- | ------------------------------- |
| Compose 文件     | `docker-compose.ai-dev.yml`     |
| Project name     | `plane-ai-dev`                  |
| API 端口         | `18180`（避免与 18080 冲突）    |
| Web 端口         | `18181`                         |
| Postgres volume  | `plane_ai_dev_pgdata`           |
| Redis volume     | `plane_ai_dev_redisdata`        |
| Container prefix | `plane-ai-dev-*`                |
| Env file         | `.env.ai-dev.local`（不提交）   |
| Env example      | `.env.ai-dev.example`（可提交） |

---

## 6. 环境变量设计

### .env.ai-dev.example（可提交，无 secret）

```bash
# Database
POSTGRES_USER=plane_ai_dev
POSTGRES_PASSWORD=replace_me
POSTGRES_DB=plane_ai_dev
PGDATA=/var/lib/postgresql/data

# Redis
REDIS_HOST=plane-ai-dev-redis
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=plane-ai-dev-mq
RABBITMQ_PORT=5672
RABBITMQ_USER=plane_ai_dev
RABBITMQ_PASSWORD=replace_me
RABBITMQ_VHOST=plane_ai_dev

# AI Feature Flags
ENABLE_AI_ASSISTANT=1
ENABLE_AI_MCP_RUNTIME=1
AI_MCP_ADAPTER=mock

# LLM (replace with real key in .env.ai-dev.local)
LLM_API_KEY=replace_me
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# MinIO
AWS_REGION=
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_S3_ENDPOINT_URL=http://plane-ai-dev-minio:9000
AWS_S3_BUCKET_NAME=uploads
FILE_SIZE_LIMIT=5242880

# Django
SECRET_KEY=replace_me_with_random_string
```

### .env.ai-dev.local（不提交，含真实 secret）

```bash
# Copy from .env.ai-dev.local and fill in real values
POSTGRES_PASSWORD=<real_password>
RABBITMQ_PASSWORD=<real_password>
SECRET_KEY=<random_string>
LLM_API_KEY=<real_key>
```

---

## 7. Secret 管理要求

| 要求                                | 实现 |
| ----------------------------------- | ---- |
| .env.ai-dev.local 加入 .gitignore   | ✅   |
| .env.ai-dev.example 不含真实 secret | ✅   |
| 不输出 secret 到报告                | ✅   |
| 不提交 secret 到 git                | ✅   |

---

## 8. Migration 策略

| 步骤 | 命令                                                                                                | 说明               |
| ---- | --------------------------------------------------------------------------------------------------- | ------------------ |
| 1    | `docker compose -f docker-compose.ai-dev.yml exec api python manage.py migrate`                     | 应用所有 migration |
| 2    | `docker compose -f docker-compose.ai-dev.yml exec api python manage.py showmigrations \| grep 0122` | 确认 0122 已应用   |
| 3    | 不对 localhost:18080 数据库运行                                                                     | 保护现有数据       |

---

## 9. 测试数据策略

| 项目           | 值                                       |
| -------------- | ---------------------------------------- |
| 测试 workspace | `ai-test`                                |
| 测试 project   | `AI Test Project` (identifier: `AITEST`) |
| 测试 issue     | `Test Issue for State Update`            |
| 测试 state A   | `Todo` (backlog group)                   |
| 测试 state B   | `In Progress` (started group)            |
| 测试用户       | workspace ADMIN                          |
| 回滚           | 测试后通过 API 恢复原 state              |

---

## 10. 后续阶段拆分

| 阶段   | 任务                             | 允许修改 Docker | 允许运行 migrate | 允许写测试数据 |
| ------ | -------------------------------- | --------------- | ---------------- | -------------- |
| 9.3.7C | Prepare isolated dev stack files | ✅ 创建新文件   | 否               | 否             |
| 9.3.7D | Build/start isolated dev stack   | ✅ 启动         | 否               | 否             |
| 9.3.7E | Apply migration + enable flags   | 否              | ✅ dev DB        | 否             |
| 9.3.7F | Create/select test data          | 否              | 否               | ✅ dev DB      |
| 9.3.8  | Manual runtime test              | 否              | 否               | ✅ dev DB      |

---

## 11. 风险清单

| 风险        | 缓解                              |
| ----------- | --------------------------------- |
| 端口冲突    | 使用 18180/18181，不与 18080 冲突 |
| Volume 冲突 | 独立命名 `plane_ai_dev_*`         |
| 数据库污染  | 独立 volume，不影响现有数据       |
| Secret 泄露 | .env.ai-dev.local 加入 .gitignore |
| 构建失败    | 使用 Dockerfile.dev（已存在）     |

---

## 12. 推荐下一步

Phase 9.3.7C：创建 `docker-compose.ai-dev.yml` 和 `.env.ai-dev.example` 文件。

---

## 13. 是否启动 Docker

**否。**

---

## 14. 是否 build 镜像

**否。**

---

## 15. 是否运行 migrate

**否。**

---

## 16. 是否修改数据

**否。**

---

## 17. 是否修改 .env

**否。**

---

## 18. 是否修改 Docker 文件

**否。** 只设计新文件。

---

## 19. 是否可以进入 Phase 9.3.7C

**是。** 设计完成，可创建 dev stack 文件。

---

## 20. Phase 9.3.7C 实施记录（2026-05-28）

Phase 9.3.7C 已创建 dev stack 配置文件，详见 [`PHASE_9_3_7C_ISOLATED_DEV_STACK_FILES_REPORT.md`](./PHASE_9_3_7C_ISOLATED_DEV_STACK_FILES_REPORT.md)。

**实施结果**：

- ✅ `docker-compose.ai-dev.yml` 创建
- ✅ `.env.ai-dev.example` 创建
- ✅ `.gitignore` 更新
