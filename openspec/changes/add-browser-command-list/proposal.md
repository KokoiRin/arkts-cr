## Why

`cr browse` 已经有过滤、scope 切换、commit review、build 控制、打开编辑器等命令，但用户只有在 README 或记忆里才知道 `:` 后能输入什么。要继续朝 terminal workbench 走，命令必须能在界面内被发现，而不是靠反复试错触发 unknown command。

## What Changes

- 增加 browser 内置命令列表视图，按用途展示可用命令和简短说明。
- 支持 `commands`、`cmds`、`help commands` 打开命令列表。
- raw-key 模式中，按 `:` 后直接回车或输入 `?` 打开命令列表。
- 命令列表作为普通 browser view 渲染，保留底部 build 面板和输入提示。
- 不实现 fuzzy search、自动补全、命令历史或第三方 command palette 框架。

## Capabilities

### New Capabilities
- `browser-command-list`: 交互式 browser 的命令发现、命令列表展示和返回行为。

### Modified Capabilities
- 无。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 mode、命令处理和命令列表渲染。
- 测试需要覆盖命令列表显示、raw command prompt 的空输入/`?` 行为、返回文件列表，以及 line mode 不产生额外噪音。
- README、`docs/design.md` 和 `docs/p0.md` 需要更新，记录 command list 作为当前 command palette 的最小形态。
