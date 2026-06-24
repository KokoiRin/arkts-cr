## Why

`cr browse` 的 review notes 已经支持写入、汇总和复制。随着一次 review 中备注增多，用户需要像 IDE 的 Problems/Bookmarks 过滤一样，快速按文件路径或备注内容缩小 notes 列表，而不是扫完整汇总。

## What Changes

- 新增 `notes QUERY` 命令，按路径或备注文本过滤当前 workspace 的 review notes。
- 匹配规则使用大小写不敏感的子串匹配。
- 过滤结果继续沿用 `notes` 的排序：当前 changed files 按 review 顺序，额外持久化路径按路径排序。
- `notes`、`copy notes`、`notes copy` 现有行为保持不变。

## Capabilities

### New Capabilities

- `browser-review-notes-search`: 定义 interactive browser 中按 query 搜索 review notes 的能力。

### Modified Capabilities

- `browser-review-notes-summary`: summary 支持可选 query，但默认仍显示全部 notes。

## Impact

- Touches `src/cr/ui/commands.py` for `notes QUERY` command parsing.
- Touches `src/cr/ui/browser.py` for filtered note summary construction and command catalog help.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
- Adds focused tests for parsing, matching, empty filtered state, raw-key feedback, and command list discoverability.
