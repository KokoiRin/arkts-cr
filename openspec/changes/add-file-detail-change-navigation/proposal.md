## Why

File Detail 已经可以跳 hunk、搜索文本、重复搜索并对当前行执行 open/copy，但在一个很大的 hunk 里，用户仍需要一行行滚动才能找到下一处真正的 `+` / `-` 改动。替代 IDE 的 review 工作流需要能在当前文件内快速穿梭实际改动行。

## What Changes

- 增加 `next change` 命令：在当前 File Detail 中跳到下一条 added/deleted 渲染行。
- 增加 `prev change` 命令：在当前 File Detail 中跳到上一条 added/deleted 渲染行。
- 搜索目标只包含实际 diff 改动行，不包含 hunk header、context 行、note/purpose/risk 等 metadata 行。
- 到达末尾/开头时在当前文件内 wraparound。
- 保持 `n` / `p` 文件导航、`next hunk` / `prev hunk`、`next match` / `prev match` 语义不变。

## Capabilities

### New Capabilities

- `file-detail-change-navigation`: File Detail 内在实际 added/deleted 改动行之间跳转。

### Modified Capabilities

无。

## Impact

- 影响 `cr.ui.file_detail_navigation`、`cr.ui.commands`、`cr.ui.command_catalog` 和 `BrowserCommandExecutor`。
- 不新增依赖，不改变渲染格式，不改变 workspace persistence。
- README、CONTEXT、design、workbench navigation、P0 记录需要补充命令说明。
