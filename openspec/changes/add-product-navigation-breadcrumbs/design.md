## 设计

当前实现的最小落点是 `_scope_context_line()`：所有 raw-key full redraw 都经过它渲染 context/status 行。新增一个小的 breadcrumb 生成函数，把产品层级映射到文本，而不是让调用点各自拼接。

## 行为映射

- `state.mode == "commits"`：显示 `Scope: recent commits`。这是 scope selection / commit picker，不进入 Files。
- `state.mode == "commands"`：显示当前 review scope 和 `Commands`，例如 `Scope: worktree > Commands`。Command Palette 是跨层动作入口，不是 review 层级，但用户需要知道自己打开的是命令面板。
- `state.mode == "list"`：显示 `Scope: <scope> > Files`。
- `state.mode == "file"`：显示 `Scope: <scope> > Files > <selected path>`。
- 如果没有可见文件或 selected 超界，File Detail 回退到 `Scope: <scope> > Files`。
- `state.status_message` 继续追加在 breadcrumb 后面。

## 模块边界

- 改动限定在 `src/cr/ui/browser.py` 的 context/status 渲染附近。
- 不触碰 `cr.review.changes`、Git scope 选择、build 生命周期或 workspace persistence。
- 测试放在现有 browser 测试附近，验证用户可见文本。

## 风险

- 长路径可能让上下文行过长。现有 `_fit_terminal_line()` 已负责裁剪；本轮复用它。
- 当前内部 mode 仍是 `list/file/commits/commands`，这和产品术语不完全一致。breadcrumb 是第一步，后续再考虑更深的 `BrowserNavigation` / `ReviewWorkspace` 模块。
