## Why

`cr browse` 的 command palette 已经覆盖导航、scope、任务、文件动作、notes 和诊断。命令数量继续增长后，仅靠原始顺序和简单包含匹配会让用户搜索时看到太多弱相关结果，也不知道当前过滤剩下多少可执行命令。

## What Changes

- 过滤 command palette 时显示匹配数量和总数。
- 过滤结果按命中质量排序：命令/标题/分组命中优先，描述命中靠后。
- 保持未过滤时的既有分组顺序和命令顺序。
- 保持 `Enter` 执行当前选中命令、`/` 过滤、`c` 清除过滤的现有语义。

## Capabilities

### New Capabilities

- `browser-command-palette-organization`: 定义 command palette 搜索结果组织和匹配反馈。

### Modified Capabilities

- `browser-command-palette-search`: 过滤行为保持可用，但增加结果计数和排序。

## Impact

- Touches `src/cr/ui/browser.py` command palette helpers.
- Updates README, design docs, navigation roadmap, and P0 notes.
- Adds focused tests for filter count, empty count, and match ranking.
