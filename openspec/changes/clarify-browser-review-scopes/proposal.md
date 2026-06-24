## Why

`cr browse` 已经能看 worktree、staged、all、base、range 和 recent commits，但这些范围主要藏在启动参数或隐式状态里。用户进入 TUI 后很容易不知道自己正在 review 哪个工作区，也缺少在会话内切换 review scope 的清晰入口。

## What Changes

- 在 browser 主界面展示当前 review scope，例如 `worktree`、`staged`、`all local changes`、`base main`、`range main..HEAD`、`commit abc12345`、`recent commits`。
- 增加会话内 scope 命令：`worktree`、`staged`、`all`、`base REF`、`range OLD..NEW`。
- 保留现有 recent commits 行为，并让 commit review 的 scope 明确显示为所选 commit。
- 切换 scope 后清空过滤、重载 changed files、重置列表位置，避免旧 scope 的 selection 泄漏到新 scope。
- 不改变 Git diff 语义，不新增第三方 TUI 依赖，不实现完整 command palette。

## Capabilities

### New Capabilities
- `browser-review-scopes`: 交互式 browser 的 review scope 可见性和会话内 scope 切换行为。

### Modified Capabilities
- 无。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 scope 状态展示、命令处理和刷新逻辑。
- 测试需要覆盖 scope header、staged/all/worktree/base/range 切换、commit scope 展示，以及旧过滤/selection 清理。
- README、`docs/design.md` 和 `docs/p0.md` 需要更新，记录新的 workspace 导航层级。
