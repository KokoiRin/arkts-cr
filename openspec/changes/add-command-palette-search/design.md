## Context

当前 browser 里已经有两种过滤需求：

- 文件列表路径过滤：`filter_text`，通过 `/` 或 `filter QUERY` 设置，作用于 `visible_changes`。
- command palette 动作过滤：本轮新增，只应作用于 commands mode。

两者不能共用同一个字段。否则用户在 command palette 里搜索 `build` 后回到文件列表，会错误地只显示 path 里包含 `build` 的文件。

## State

`BrowserState` 新增：

- `command_filter_text: str`

派生函数：

- `_filtered_command_palette_entries(state)`：从 `_command_palette_entries()` 中按 `command_filter_text` 做 case-insensitive substring 过滤。

匹配字段：

- group，例如 `Build task`
- label，例如 `rerun / rebuild`
- command，例如 `rerun`
- description，例如 `run build again`

## Commands

Raw-key commands mode:

- `/`：显示 `command filter> ` 输入，写入 `state.command_filter_text`。
- `c` / `clear`：清空 `state.command_filter_text`。
- ↑/↓ / j/k、Home/End：在过滤后的列表里移动。
- Enter/→/l：执行过滤后选中的 command。

Line mode:

- 保留现有 `commands` 的只读完整命令说明。
- 不增加 line mode 中的可交互 palette search。

## Boundaries

- 不实现 fuzzy scoring。
- 不高亮匹配片段。
- 不把 command filter 写入 workspace state。
- 不改变文件路径 filter 语义。

## Test Plan

- 单元测试 `_filtered_command_palette_entries()` 能按 group/label/command/description 匹配。
- 渲染测试：过滤后只显示匹配命令，并显示 filter 状态。
- 集成测试：commands mode 中 `/` 设置 command filter，不修改 `filter_text`。
- 集成测试：commands mode 中 `c` 清 command filter，不清文件 filter。
- 集成测试：过滤后 Enter 执行过滤结果中的命令。
