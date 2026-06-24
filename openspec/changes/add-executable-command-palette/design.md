## Context

现有 `commands` mode 使用 `_browse_command_lines()` 展示 `_command_catalog()`。catalog 是纯文本，部分 entry 只是说明（如 `Enter / 1..N`、`base REF`），没有稳定的可执行命令字段。主循环里所有命令都是字符串分支处理；这意味着最小实现应继续复用字符串命令，不新建 action registry。

当前风险点：

- `BrowserState.clamp_selection()` 在 `commands` mode 下使用 `visible_changes` 的长度，导致 commands 页面没有自己的 selection 范围。
- Enter 在 `commands` mode 下没有专门处理，可能因为存在 visible changes 而进入文件模式。
- command list 是产品入口，但现在只能读，不能操作。

## Goals / Non-Goals

**Goals:**

- 为 command palette 提供可执行 entry 列表，每条 entry 有 label、description 和 command string。
- `commands` mode 使用自己的 selection 范围和 scroll。
- Enter 在 `commands` mode 中执行选中的 command string。
- 执行后复用现有 command loop，保持 `build`、`staged`、`remaining` 等行为一致。
- 保留非 TTY `commands` 输出，不要求行模式可选择。

**Non-Goals:**

- 不做 fuzzy search。
- 不执行需要参数的命令模板，例如 `base REF`、`range OLD..NEW`。
- 不引入插件式 command registry。
- 不改 `:` command prompt 的输入语义。

## Decisions

### Decision: command palette entries 是 catalog 的可执行子集

新增轻量 `PaletteCommand`，只包含 `label`、`command`、`description` 和 `group`。`_command_palette_entries()` 从 `_command_catalog()` 派生，过滤掉无法直接执行的说明项，避免 command list 和 palette 两套文案漂移。

### Decision: 用 pending command 复用主循环

当 commands mode 中按 Enter 时，不直接调用 build/scope 函数，而是把选中的 command string 作为下一轮要处理的命令。这样所有命令仍走同一段分支逻辑，减少行为分叉。

### Decision: commands mode selection 独立于文件 selection

`BrowserState` 新增 `command_selected` 和 `command_scroll`。文件列表的 `selected` 保持不变；进入/退出 commands mode 不打乱当前文件选择。

## Test Plan

- 单元测试：command palette entries 只包含可执行命令，并包含 `build`、`staged`、`remaining` 等核心动作。
- 单元测试：commands screen 显示选中 marker，并随 command selection 移动。
- 集成测试：raw-key commands mode 按 Enter 执行 `build`，不会打开文件。
- 集成测试：commands mode 中 b/left 返回 list 且保留文件 selection。
