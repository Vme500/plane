# 第 9.3.8A-2R4 阶段报告：API 502 Recovery

> 日期：2026-06-02
> 分支：feat/ai-phase-6-mcp-readonly-runtime
> 状态：修复完成

---

## 1. 当前分支和 commit

| 项目        | 值                                                             |
| ----------- | -------------------------------------------------------------- |
| 分支        | `feat/ai-phase-6-mcp-readonly-runtime`                         |
| 最新 commit | `575a2bb19e` — `docs: validate isolated AI dev instance setup` |
| 工作区状态  | 有未提交 docs 报告                                             |

---

## 2. 用户问题

- `http://localhost:18181/` 显示 "Plane didn't start up correctly"
- `http://localhost:18181/api/instances/` 返回 502 Bad Gateway

---

## 3. Root Cause

**nginx 缓存了 API 容器的旧 IP 地址。**

Phase 9.3.8A-2R3 重启了 API 容器，导致 API 容器获得新 IP（172.20.0.6），但 nginx 仍尝试连接旧 IP（172.20.0.5），返回 "Connection refused"。

---

## 4. 修复

重启 Web 容器，使 nginx 重新解析 API 主机名。

---

## 5. 修复前后对比

| 检查项                 | 修复前 | 修复后 |
| ---------------------- | ------ | ------ |
| `18180/api/instances/` | 200    | 200    |
| `18181/api/instances/` | 502    | 200    |
| issue state            | Todo   | Todo   |
| ai.write.executed      | 0      | 0      |

---

## 6. 修改文件清单

无代码修改。只重启 Web 容器。

---

## 7. 是否可以进入 Phase 9.3.8A-3

**是。** API 和 Web proxy 均恢复正常。

---

## 8. Phase 9.3.8A-2R5 修复记录（2026-06-02）

Phase 9.3.8A-2R5 修复了 CSRF 登录问题，详见 [`PHASE_9_3_8A_2R5_CSRF_LOGIN_FIX_REPORT.md`](./PHASE_9_3_8A_2R5_CSRF_LOGIN_FIX_REPORT.md)。

**修复**：

- Root cause：`CSRF_TRUSTED_ORIGINS` 为空
- 添加 `CSRF_TRUSTED_ORIGINS=http://localhost:18181`
