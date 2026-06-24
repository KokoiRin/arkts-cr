## 为什么

`docs/workbench-navigation.md` 已经把产品导航定为 `Review Scope -> Changed Files -> File Detail`，但当前 `cr browse` 的上下文行仍只显示 `Scope: worktree`、`Scope: commit ...` 这类一级信息。用户进入文件树或单文件详情后，仍需要靠内部 prompt 和记忆判断自己处在哪一层。

为了让产品层级真正落到体验里，需要在 context/status 层显示 breadcrumb，让用户始终看到当前 Review Scope、Changed Files 层和 File Detail 层。

## 改什么

- 将 raw-key/full redraw 的上下文行从单一 scope label 升级为产品 breadcrumb。
- Changed Files 层显示：`Scope: <scope> > Files`。
- File Detail 层显示：`Scope: <scope> > Files > <path>`。
- Commit picker 保持一级 scope selection 语义，显示 `Scope: recent commits`。
- 保留状态反馈：`Scope: worktree > Files | Opened ...`。

## 不做

- 不重写 browser mode/state 结构。
- 不新增 Scope Home 页面。
- 不改变文件树、diff、build panel 或 command palette 的行为。
- 不改变非 raw line mode 的命令语义。
