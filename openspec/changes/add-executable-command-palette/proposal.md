## Why

`cr browse` 的长期方向是 terminal workbench，而不是一组需要记忆的命令。当前 `commands` 模式只能展示说明文字，用户仍然需要退出列表、记住命令、再输入命令；更糟的是 raw-key 模式下在 `commands` 页面按 Enter 仍可能落到文件打开逻辑，页面层级和操作语义不一致。

IDE 式工作台需要一个可靠的 command palette：用户能打开命令列表、上下选择一个动作、按 Enter 执行。后续再做搜索、快捷键提示、任务历史时，都可以建立在这个入口上。

## What Changes

- 将 `commands` 模式从只读帮助页升级为可选择的 command palette。
- command palette 只列出可直接执行的命令；带参数的命令（如 `base REF`、`range OLD..NEW`）继续保留在文字说明或 `:` 命令输入里。
- raw-key 模式下，`commands` 页面支持 ↑/↓ / j/k 移动，Enter 执行当前命令，b/← 返回文件列表。
- 在 command palette 中执行命令时，复用现有命令处理路径，避免为每个命令复制一套行为。
- 文档说明 `: commands` 是可执行入口，而不仅是帮助页。

## Capabilities

### New Capabilities
- `browser-command-palette`: 可选择、可执行的 browser 命令入口。

### Modified Capabilities
- `browser-command-list`: 从只读列表升级为 executable command palette。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 command catalog、commands mode 渲染、selection clamp 和 Enter handling。
- 测试需要覆盖 commands mode 选择移动、Enter 执行、commands mode 不误打开文件、非 TTY 行模式仍能打印命令列表。
- 不引入第三方 TUI 框架，不做模糊搜索。
