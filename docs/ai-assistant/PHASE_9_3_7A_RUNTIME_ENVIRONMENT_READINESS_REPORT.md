# 第 9.3.7A 阶段报告：Runtime Environment Readiness

> 日期：2026-05-28
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：调研完成，环境不兼容

---

## 1. 当前分支和 commit

| 项目        | 值                                                                    |
| ----------- | --------------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                                |
| 最新 commit | `fa81533d1c` — `docs: prepare confirmed AI state update runtime test` |
| 工作区状态  | 干净（无未提交修改）                                                  |

---

## 2. localhost:18080 代码来源检查

| 检查项                        | 结果                                               |
| ----------------------------- | -------------------------------------------------- |
| 服务来源                      | `plane-app-proxy-1` (makeplane/plane-proxy:v1.3.1) |
| 后端容器                      | `plane-app-api-1` (makeplane/plane-backend:v1.3.1) |
| 镜像来源                      | **官方 Docker Hub 镜像**，非当前 fork 构建         |
| 运行代码是否来自当前 fork     | **否**                                             |
| 容器内 `/code/plane/ai/` 目录 | **不存在**                                         |
| 容器内 MCP/AI 模块            | **不存在**                                         |

**结论**：localhost:18080 运行的是官方 Plane v1.3.1，不包含 Phase 6-9.3 的任何改动。

---

## 3. 是否运行当前 fork 分支代码

**否。** 官方 Docker 镜像 `makeplane/plane-backend:v1.3.1` 不包含我们的 AI/MCP 代码。

---

## 4. 数据库环境检查

| 检查项                            | 结果                                          |
| --------------------------------- | --------------------------------------------- |
| 数据库容器                        | `plane-app-plane-db-1` (postgres:15.7-alpine) |
| 是否生产数据                      | ⚠️ 可能包含真实数据（自托管环境）             |
| 是否可视为 dev/staging            | **不确定**                                    |
| AIAuditEvent migration 是否已应用 | **否**（容器内无 AI 模块）                    |

---

## 5. Migration 0122 应用状态

**未应用。** 官方镜像不包含 AIAuditEvent model，migration 0122 不存在于运行环境中。

---

## 6. Feature Flags 状态

| Flag                    | 值    | 原因                    |
| ----------------------- | ----- | ----------------------- |
| `enable_ai_assistant`   | None  | 官方 v1.3.1 不含此 flag |
| `enable_ai_mcp_runtime` | None  | 官方 v1.3.1 不含此 flag |
| `has_llm_configured`    | False | 未配置 LLM_API_KEY      |

---

## 7. LLM 配置状态

`has_llm_configured=false` 原因：Docker 环境未设置 `LLM_API_KEY` 环境变量。

---

## 8. 现有环境是否可作为 dev/staging

**否。** 原因：

1. 运行官方镜像，不含 fork 代码
2. 数据库可能包含真实数据
3. 无法直接应用 fork migration
4. 无法直接启用 fork feature flags

---

## 9. 方案 A / B 比较

### 方案 A：使用现有 localhost:18080 环境

| 项目     | 说明                             |
| -------- | -------------------------------- |
| 适用条件 | ❌ 不适用                        |
| 原因     | 官方镜像不含 fork 代码，无法测试 |
| 风险     | 高（修改生产环境）               |
| 结论     | **不推荐**                       |

### 方案 B：单独启动 dev/staging stack

| 项目     | 说明                                             |
| -------- | ------------------------------------------------ |
| 适用条件 | ✅ 适用                                          |
| 方式     | 从当前 fork 分支构建 Docker 镜像，使用独立数据库 |
| 优点     | 安全隔离，不影响现有环境                         |
| 缺点     | 耗时较高，需要构建镜像                           |
| 结论     | **推荐**                                         |

---

## 10. 推荐方案

**方案 B：单独启动 dev/staging stack。**

理由：

1. 当前环境运行官方镜像，不含 fork 代码
2. 数据库可能包含真实数据，不适合测试
3. 需要应用 fork migration + 启用 fork feature flags
4. 独立 stack 可安全创建测试数据

---

## 11. 下一步最小操作清单

| 步骤 | 说明                                         | 状态      |
| ---- | -------------------------------------------- | --------- |
| 1    | 从 fork 分支构建 backend Docker 镜像         | ❌ 未执行 |
| 2    | 创建 docker-compose.dev.yml 使用独立数据库   | ❌ 未执行 |
| 3    | 启动 dev stack                               | ❌ 未执行 |
| 4    | 应用 migration 0122                          | ❌ 未执行 |
| 5    | 设置 `ENABLE_AI_ASSISTANT=1`                 | ❌ 未执行 |
| 6    | 设置 `ENABLE_AI_MCP_RUNTIME=1`               | ❌ 未执行 |
| 7    | 配置 LLM_API_KEY（或确认 mock adapter 可用） | ❌ 未执行 |
| 8    | 创建测试 workspace/project/issue             | ❌ 未执行 |
| 9    | 生成 proposed_action                         | ❌ 未执行 |
| 10   | 进入 Phase 9.3.8 手动测试                    | ❌ 未执行 |

---

## 12. 是否执行 Confirm

**否。**

---

## 13. 是否修改数据

**否。**

---

## 14. 是否运行 migrate

**否。**

---

## 15. 是否修改 Docker

**否。**

---

## 16. 是否修改 .env

**否。**

---

## 17. 是否可以进入环境启用阶段

**有条件。** 需要先构建 fork Docker 镜像并启动独立 dev stack。当前环境不兼容 fork 代码。

---

## 18. Phase 9.3.7B 设计记录（2026-05-28）

Phase 9.3.7B 设计了独立 fork dev stack，详见 [`PHASE_9_3_7B_ISOLATED_DEV_STACK_DESIGN.md`](./PHASE_9_3_7B_ISOLATED_DEV_STACK_DESIGN.md)。

**设计结论**：

- `docker-compose.ai-dev.yml` 使用独立 volume/端口
- API 端口 18180
- AI flags 已设计
- Migration 策略已设计
