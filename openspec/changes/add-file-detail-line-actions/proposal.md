## Why

File Detail 已经支持 hunk 跳转、文本查找和重复查找，但用户滚动或搜索到某个具体渲染行后，还不能像在 IDE 里一样直接对“当前行”执行打开或复制锚点。现在 `open` / `copy anchor` 仍偏向文件级首个改动行，`open hunk` / `copy hunk` 又偏向整个 hunk。

## What Changes

- 增加 `open line` 命令：在 File Detail 中打开当前可见渲染行对应的新文件行号。
- 增加 `copy line` 命令：在 File Detail 中复制当前可见渲染行对应的 `path:line`。
- 从已渲染的 File Detail 行文本解析新文件行号，支持 hunk header、context 行和 added 行。
- 对 deleted 行、文件头、purpose/note/risk 等没有新文件行号的位置报告明确空状态。
- 保持现有 `open`、`copy anchor`、`open hunk`、`copy hunk` 行为不变。

## Capabilities

### New Capabilities

- `file-detail-line-actions`: File Detail 中针对当前渲染行的新文件行号执行 open/copy anchor。

### Modified Capabilities

无。

## Impact

- 影响 `cr.ui.file_detail_navigation`、`cr.ui.selected_file_actions`、`cr.ui.commands`、`cr.ui.command_catalog` 和 `BrowserCommandExecutor`。
- 不新增运行时依赖，不改变 workspace persistence schema。
- 文档需要补充 File Detail 当前行操作的使用方式。
