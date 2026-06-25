## Why

`cr browse` 已经支持标记文件已看，也支持切到下一个文件，但连续 review 时用户需要反复执行 `m` 再 `n`/Enter。作为 IDE-like workbench，读完一个文件后应有一个原子动作：标记当前文件完成并前进到下一个待看的文件。

## What Changes

- 增加 `done next` / `seen next` 命令：标记当前 visible changed file 为 seen，并移动到下一个可见文件。
- 在 Changed Files 层执行时保持在 Changed Files，只移动选择。
- 在 File Detail 层执行时保持在 File Detail，并打开下一个文件详情。
- 在 `remaining` 过滤下，标记当前文件后按更新后的可见 remaining 列表选择下一个文件，避免跳过文件。
- 到最后一个文件时保留在最后/当前可用文件并给出稳定状态消息。

## Capabilities

### New Capabilities

- `done-next-review-flow`: 连续 review 中一键标记当前文件 seen 并前进到下一个文件。

### Modified Capabilities

无。

## Impact

- 影响 `cr.ui.commands`、`cr.ui.command_catalog` 和 `BrowserCommandExecutor` 的 progress/navigation action。
- 不改变 Review Workspace persistence schema；继续复用 `seen_paths` 和现有 selected file state。
- 文档需要补充连续 review 的使用方式。
