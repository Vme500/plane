# 第 9.3.7C 阶段报告：Isolated Fork Dev Stack Files

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：文件创建完成，未启动 Docker

---

## 1. 当前分支和 commit

| 项目       | 值                                                  |
| ---------- | --------------------------------------------------- |
| 分支       | `feat/ai-phase-6-mcp-readonly-runtime`              |
| 基于       | `cb3b765265` — `docs: design isolated AI dev stack` |
| 工作区状态 | 干净（无未提交修改）                                |

---

## 2. 新增/修改文件清单

| 文件                        | 变更                            |
| --------------------------- | ------------------------------- |
| `docker-compose.ai-dev.yml` | 新增：独立 dev stack compose    |
| `.env.ai-dev.example`       | 新增：环境变量模板（无 secret） |
| `.gitignore`                | 修改：添加 `.env.ai-dev.local`  |

---

## 3. docker-compose.ai-dev.yml 说明

| 服务                  | 说明                          |
| --------------------- | ----------------------------- |
| `plane-ai-dev-api`    | Backend API，从 fork 源码构建 |
| `plane-ai-dev-web`    | Frontend，从 fork 源码构建    |
| `plane-ai-dev-db`     | PostgreSQL 15.7               |
| `plane-ai-dev-redis`  | Valkey 7.2.11                 |
| `plane-ai-dev-worker` | Celery worker                 |

---

## 4. .env.ai-dev.example 说明

- 可提交到 git
- 所有 secret 使用 placeholder（`change-me-local-only`, `replace-me`）
- 包含 AI flags: `ENABLE_AI_ASSISTANT=1`, `ENABLE_AI_MCP_RUNTIME=1`
- 包含 `AI_MCP_ADAPTER=mock`
- 包含 `LLM_API_KEY=replace-me`

---

## 5. .gitignore 变更

添加 `.env.ai-dev.local` 到忽略列表，防止真实 secret 被提交。

---

## 6. 端口设计

| 服务       | 外部端口 | 内部端口 |
| ---------- | -------- | -------- |
| API        | 18180    | 8000     |
| Web        | 18181    | 3000     |
| PostgreSQL | 15432    | 5432     |
| Redis      | 16379    | 6379     |

---

## 7. Volume 设计

| Volume                   | 用途                 |
| ------------------------ | -------------------- |
| `plane_ai_dev_pgdata`    | 独立 PostgreSQL 数据 |
| `plane_ai_dev_redisdata` | 独立 Redis 数据      |

---

## 8. Compose Project Name

`plane-ai-dev`（通过 `-p plane-ai-dev` 参数指定）

---

## 9. 如何复制 env example 到 local env

```bash
cp .env.ai-dev.example .env.ai-dev.local
# Edit .env.ai-dev.local with real values
```

---

## 10. 后续如何 build/start（Phase 9.3.7D）

```bash
docker compose -f docker-compose.ai-dev.yml -p plane-ai-dev up -d --build
```

---

## 11. 后续如何 migrate（Phase 9.3.7E）

```bash
docker compose -f docker-compose.ai-dev.yml -p plane-ai-dev exec plane-ai-dev-api python manage.py migrate
```

---

## 12. 后续如何创建测试数据（Phase 9.3.7F）

通过 API 或 Django shell 创建测试 workspace/project/issue。

---

## 13. Secret 管理要求

| 要求                                  | 实现 |
| ------------------------------------- | ---- |
| `.env.ai-dev.local` 加入 .gitignore   | ✅   |
| `.env.ai-dev.example` 不含真实 secret | ✅   |
| 不输出 secret 到报告                  | ✅   |

---

## 14. 是否启动 Docker

**否。**

---

## 15. 是否 build 镜像

**否。**

---

## 16. 是否运行 migrate

**否。**

---

## 17. 是否修改数据

**否。**

---

## 18. 是否修改生产目录

**否。**

---

## 19. 是否可以进入 Phase 9.3.7D

**是。** 文件创建完成，可启动 dev stack。

---

## 20. Phase 9.3.7D 启动记录（2026-05-28）

Phase 9.3.7D 尝试启动 dev stack，详见 [`PHASE_9_3_7D_ISOLATED_DEV_STACK_START_REPORT.md`](./PHASE_9_3_7D_ISOLATED_DEV_STACK_START_REPORT.md)。

**结果**：

- ✅ `.env.ai-dev.local` 创建
- ✅ `docker compose config` 通过
- ✅ 修复 build context 路径
- ⚠️ Build 失败：网络超时
