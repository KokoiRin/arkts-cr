## Why

`cr browse` 已经能在一个 Review Scope 里看 Changed Files、进入 File Detail、标记 seen/todo，并且持久化 review workspace。下一步要更像 IDE review 工作台，需要允许用户在当前文件上留下轻量备注：为什么要回来看、风险点是什么、或者后续要问谁。

## What Changes

- 新增 `note TEXT` 浏览器命令，为当前选中文件写入一条短备注。
- 新增空 `note` 命令，清除当前选中文件的备注。
- 在 Changed Files 文件树和 File Detail 头部展示当前文件备注。
- 将备注保存在 `.git/cr/browse-state.json`，和 seen/todo 进度一样跟随默认 browse workspace 恢复。

## Capabilities

### New Capabilities

- `browser-review-notes`: 定义 interactive browser 的 per-file review note 能力。

### Modified Capabilities

- `browser-workspace-persistence`: workspace state 增加 per-file note 持久化，但不影响 task history。

## Impact

- Touches `src/cr/ui/workspace.py` for review note state and persistence.
- Touches `src/cr/ui/commands.py` for `note` command parsing.
- Touches `src/cr/ui/browser.py` for command execution and rendering.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
- Adds focused tests for command parsing, workspace persistence, rendering, and action execution.
