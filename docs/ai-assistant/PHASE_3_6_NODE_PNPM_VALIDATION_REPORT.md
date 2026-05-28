# 第 3.6 阶段报告：Node/pnpm 安装与验证

> 日期：2026-05-28
> 分支：feat/ai-phase-3-pi-chat-page
> HEAD: 8083c60cf6 — docs: validate minimal pi-chat page

---

## 1. Node 安装方式

nvm 已预装（v0.40.3）。项目已有 Node v24.16.0（通过 nvm 管理），满足项目要求 >= 22.18.0。无需额外安装。

---

## 2. Node 版本

```
v24.16.0
```

---

## 3. pnpm 版本

项目要求 `pnpm@10.32.1`（通过 `packageManager` 字段指定）。

通过 corepack 准备并激活：

```bash
corepack enable
corepack prepare pnpm@10.32.1 --activate
```

```
pnpm 10.32.1
```

---

## 4. 是否执行 pnpm install --frozen-lockfile

**是。** 执行成功，所有依赖安装完成。

---

## 5. 是否修改 lockfile

**否。** `git diff pnpm-lock.yaml` 无输出。

---

## 6. 执行了哪些 typecheck / lint 命令

| 命令                                       | 说明                                                                                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `pnpm turbo run build --filter='@plane/*'` | 构建所有 workspace 依赖包（@plane/types, @plane/constants, @plane/propel, @plane/ui, @plane/services, @plane/i18n, @plane/editor 等） |
| `pnpm --filter web check:types`            | `react-router typegen && tsc --noEmit`                                                                                                |
| `pnpm --filter web check:lint`             | `oxlint --max-warnings=11957 .`                                                                                                       |

---

## 7. 验证结果

### typecheck

**通过。** exit code 0，无类型错误。

唯一的 warning（非阻塞）：

```
[MODULE_TYPELESS_PACKAGE_JSON] Warning: Module type of file:///.../packages/tailwind-config/postcss.config.js is not specified
```

这是项目预存问题，与 pi-chat 代码无关。

### lint

**通过。** 0 errors，998 warnings（阈值 11957）。

pi-chat 相关 warning（1 个）：

```
app/(all)/[workspaceSlug]/(projects)/pi-chat/page.tsx:97:19
  ! eslint-plugin-react(no-array-index-key): Usage of Array index in keys is not allowed
```

使用 `key={idx}` 作为消息列表 key。这是 best-practice 警告，非错误。聊天消息通常只追加不重排，使用 index 作为 key 不会导致问题。与其他文件中的同类警告一致（如 cycles/detail/page.tsx）。

---

## 8. 如果失败，失败原因

首次 typecheck 失败（4992 个错误），原因是 workspace 包（`@plane/types`、`@plane/propel` 等）未构建，TypeScript 无法解析模块声明。

**修复**：先执行 `pnpm turbo run build --filter='@plane/*'` 构建所有 workspace 包，再运行 typecheck 即可通过。

---

## 9. 是否做了小修复

**否。** typecheck 和 lint 均通过，无需修复。

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

## 14. 是否可以进入第 4 阶段

**可以。** typecheck 和 lint 均通过，pi-chat 页面代码验证完成。
