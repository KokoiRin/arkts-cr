## Context

`BrowserState.visible_changes` 是 browser 列表、数字选择、next/previous、editor opening 的共同入口。progress filtering 应该落在这里，而不是分别改每个命令。已有 `filter_text` 是 path 过滤；`remaining_only` 可以在 path 过滤之后再过滤 seen paths。

## State

`BrowserState` 新增：

- `seen_paths: set[str]`
- `remaining_only: bool`

workspace state JSON 新增：

```json
{
  "seen_paths": ["src/App.ts"],
  "remaining_only": true
}
```

保存时只保存当前 review scope 下的 Git path 字符串。恢复时忽略非字符串值，并允许 paths 不再存在；不存在的 seen path 不会显示，但保留在状态里不影响启动。

## Commands

- `m` / `seen` / `done`: mark selected visible file as seen.
- `todo` / `unseen` / `unmark`: remove selected visible file from seen.
- `remaining`: show only files not in `seen_paths`.
- `allfiles` / `show all`: show all files again while keeping seen markers.

`u` 已经用于 PageUp，不复用为 unseen，避免键位冲突。

## Rendering

List mode:

- context line includes `Progress: X/Y seen`.
- rows include `[x]` for seen files and `[ ]` for unseen files.
- remaining-only mode includes `remaining only` in the filter/progress line.

File mode:

- file header includes `seen` or `todo`.

## Boundaries

- 不实现批量 mark all / unmark all。
- 不实现跨 scope 自动清理 seen paths。
- 不改变 `cr review --seen` / `--remaining`。
- 不引入新的状态文件；复用 browser workspace state。
