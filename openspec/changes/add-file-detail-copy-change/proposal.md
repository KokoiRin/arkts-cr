## Why

File Detail 已经能跳到下一条实际改动行，但用户定位到某个 `+` / `-` 行后，只有 `copy line` 的新文件锚点或 `copy hunk` 的整块上下文可用。日常 review 里经常只想把当前这条改动行发给 AI 或同事，需要一个比 hunk 更轻、比 anchor 更有内容的复制动作。

## What Changes

- 增加 `copy change` 命令：在 File Detail 中复制当前实际改动行的 compact review 片段。
- 从已渲染的 File Detail 行文本解析当前改动行类型、旧行号、新行号和清洗后的行内容。
- 对 context、hunk header、metadata、文件头等非改动行报告明确空状态。
- 保持 `copy line`、`copy hunk`、`next change` / `prev change` 既有行为不变。

## Capabilities

### New Capabilities

- `file-detail-copy-change`: File Detail 中复制当前实际 added/deleted 改动行的 review 上下文。

### Modified Capabilities

无。

## Impact

- 影响 `cr.ui.file_detail_navigation`、`cr.ui.selected_file_actions`、`cr.ui.commands`、`cr.ui.command_catalog` 和 `BrowserCommandExecutor`。
- 不新增运行时依赖，不改变 workspace persistence schema。
- 文档需要补充 File Detail 当前改动行复制的使用方式。
