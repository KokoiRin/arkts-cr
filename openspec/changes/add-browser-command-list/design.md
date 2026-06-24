## Context

`cr browse` 的可用命令已经覆盖导航、过滤、scope 切换、commit review、build 任务和打开编辑器。当前帮助区只能提示 `:` 是命令入口，unknown command 也只给一行压缩提示。随着命令变多，用户需要一个不离开 TUI 的命令索引。

## Goals / Non-Goals

**Goals:**

- 提供一个内置命令列表视图，展示常用命令、别名和简短说明。
- 让 `commands`、`cmds`、`help commands` 打开命令列表。
- raw-key 模式下，`:` 后空输入或 `?` 打开命令列表。
- 命令列表沿用 browser 主内容区渲染，保留底部 build 面板和输入提示。
- 从命令列表按 `b` / `back` 回到文件列表。

**Non-Goals:**

- 不实现 fuzzy search、补全、命令历史或可执行菜单。
- 不引入 prompt_toolkit、Textual、curses 等 TUI 框架。
- 不改变现有命令语义。
- 不把命令列表抽成跨 package 公共 API。

## Decisions

### Decision: 使用 `commands` mode，而不是弹窗或 overlay

命令列表作为 browser 的一个普通 mode 渲染到主内容区。这样可以复用已有 screen layout、build panel 和 prompt 行，不需要新增 overlay 生命周期。

备选方案是弹出浮层。它更像 IDE command palette，但当前终端渲染还没有 overlay 基础，容易重新引入屏幕错位问题。

### Decision: 命令列表是只读索引，不执行菜单项

本轮只解决发现性：用户看见命令后仍通过 `:` 输入执行。这样不需要新增 selection state，也不会和文件列表 selection 混在一起。

备选方案是做可选择菜单，回车执行。它体验更完整，但会引入命令 item、参数输入和错误处理，超出当前 P0。

### Decision: 命令条目集中定义

用一个局部 helper 返回命令分组和条目，命令列表、README 和后续 help 可以对齐这份结构。当前不强制所有 command branch 自动生成，先保持简单可读。

## Risks / Trade-offs

- [Risk] 命令列表可能和真实命令分支漂移。→ Mitigation：测试覆盖关键命令分组和 README 归档；后续若命令继续变多，再把 command dispatch 和 catalog 收敛到同一结构。
- [Risk] 新增 `commands` mode 会让 `b` 语义多一个返回目标。→ Mitigation：只让它返回 list，不尝试恢复进入前的 file/commit view，保持简单可预测。
- [Risk] 空 command prompt 在 raw 模式下改变为打开命令列表。→ Mitigation：空输入过去没有有用行为；新行为更符合 command discoverability。
