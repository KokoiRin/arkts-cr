## Why

`cr browse` 已经能恢复 review workspace，但用户在大 diff 里仍然缺少一个关键 IDE 式动作：标记“这个文件看过了”，然后只看剩余文件。现在非交互式 `cr review` 有 `--seen` / `--remaining`，但 browse 会话里没有同等能力，用户只能靠记忆或退出重新跑命令。

## What Changes

- browser 内支持把当前文件标记为 seen / done。
- 支持取消当前文件的 seen 标记。
- 支持切到 remaining-only 视图，只显示未看文件。
- 支持回到全部文件视图。
- seen paths 和 remaining-only 状态随 browser workspace 一起持久化到 `.git/cr/browse-state.json`。
- 文件列表和文件 diff 显示当前 review progress，让用户知道已看/剩余数量。

## Capabilities

### New Capabilities
- `browser-progress-markers`: browser 内 per-file seen/done 标记和 remaining 过滤。

### Modified Capabilities
- `browser-workspace-persistence`: 状态文件额外保存 seen paths 和 remaining-only 视图开关。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 `BrowserState.visible_changes`、命令处理、list/file 渲染和 workspace state 序列化。
- 测试需要覆盖 mark/unmark、remaining 过滤、列表/文件视图进度展示、持久化恢复。
- 不改变 `cr review --seen` / `--remaining` 的非交互式行为。
