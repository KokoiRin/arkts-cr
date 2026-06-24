## 为什么

`cr` 的产品导航已经定义为 `Review Scope -> Changed Files -> File Detail`，breadcrumb 也已经让层级可见。但 Review Scope 仍然主要散落在命令里：`g` 打开 recent commits，`staged` / `all` / `worktree` 需要记命令，`base` / `range` 只能靠用户知道参数格式。

为了让 Scope 真正成为一级页面，需要提供一个 Scope Home：用户可以打开一个页面看到当前可进入的变化集合，并从那里进入 worktree、staged、all local changes、recent commits，同时看到 base/range 的参数化入口。

## 改什么

- 新增 `scopes` / `scope` 命令，打开 Review Scope Home。
- Scope Home 显示一级 scope 入口：
  - Worktree
  - Staged
  - All local changes
  - Recent commits
  - Base ref
  - Explicit range
- 可执行入口支持键盘选择和 Enter。
- `base REF` / `range OLD..NEW` 这类参数化入口先作为提示显示，仍通过 `:` 命令输入，不在本轮做 inline 参数输入。
- breadcrumb/context 显示 `Scope: scope home`，不追加 `> Files`。

## 不做

- 不重写现有 scope 切换逻辑。
- 不改变 `g` / `worktree` / `staged` / `all` / `base` / `range` / Home key 等现有命令。
- 不实现 base/range 的表单输入。
- 不抽出新的导航模块；本轮先让产品层级落在 UI 上。
