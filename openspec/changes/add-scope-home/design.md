## 设计

当前 `src/cr/ui/browser.py` 已经集中拥有 interactive browse 的状态和命令循环。Scope Home 先作为 `state.mode == "scopes"` 的一级页面实现，避免在产品层级还没稳定时抽出新的 module。

## UI 行为

- `scopes`、`scope` 打开 Scope Home。`home` 继续保留为 Home key / jump-to-top 行为，避免破坏既有导航。
- Scope Home 使用上下箭头 / `j/k` 选择。
- Enter / right / `l` 对可执行 scope 入口执行现有命令语义：
  - Worktree -> `_switch_review_scope(... worktree ...)`
  - Staged -> `_switch_review_scope(... staged ...)`
  - All local changes -> `_switch_review_scope(... all ...)`
  - Recent commits -> `_load_recent_commits()` 并进入 `commits`
- Base ref 和 explicit range 在本轮显示为 parameterized hints，不执行，避免引入半成品输入状态。
- `b` / left 从 Scope Home 回到 Changed Files。

## 架构取舍

- 新增小的 `ScopeHomeEntry` 数据类和 `_scope_home_entries()`，它是 UI adapter，不是长期跨语言接口。
- 长期语言无关接口仍然是 `Review Scope`、`Changed Files`、`File Detail` 这些产品术语。
- 后续如果要换语言或大改架构，应把 `ReviewWorkspace` / `BrowserNavigation` 作为更深 module，让它隐藏 scope/list/file transitions；本轮不提前抽，因为 seam 目前只有一个 adapter。

## 测试策略

测试用户可见行为：

- Scope Home 渲染所有一级入口。
- Enter 可进入 staged/all/worktree/recent commits。
- 参数化入口显示提示但不伪装成可直接执行。
- breadcrumb 不把 Scope Home 当成 Files 层。
