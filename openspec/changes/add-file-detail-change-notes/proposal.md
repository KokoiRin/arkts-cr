## Why

File Detail 已经能跳到、打开、复制当前 hunk/line/change，但 review 中还有一个高频动作：看到某一条具体改动后立刻留下待跟进备注。现有 `note TEXT` 只能给整个文件写备注，用户需要手动补行号，容易断上下文。

## What Changes

- 增加 `note change TEXT` 命令：在 File Detail 中把当前实际 `+` / `-` 改动行的位置和备注文本写入当前文件的 review note。
- added 行备注使用 `line N: TEXT`，deleted 行备注使用 `old line N: TEXT`。
- 如果当前文件已有 review note，新改动行备注追加到同一个 per-file note 中，而不是覆盖。
- 对非改动行、空文本、File Detail 外执行给出明确状态消息。
- 保持 `note TEXT`、`note`、`notes`、`copy notes` 既有语义不变。

## Capabilities

### New Capabilities

- `file-detail-change-notes`: File Detail 中针对当前实际改动行追加 per-file review note。

### Modified Capabilities

无。

## Impact

- 影响 `cr.ui.file_detail_navigation`、`cr.ui.selected_file_actions`、`cr.ui.commands`、`cr.ui.command_catalog` 和 `BrowserCommandExecutor`。
- 不新增 review note persistence schema；继续复用 path-keyed per-file notes。
- 文档需要补充当前改动行备注的使用方式。
