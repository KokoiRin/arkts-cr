## Why

`cr browse` 的 selected-file actions 已经覆盖 `open`、`copy path`、`copy anchor`、`reveal` 和 `file actions` 诊断。现在 `copy` / `reveal` 的平台命令解析与执行在 `cr.ui.file_actions`，但 editor handoff 的 `open` 仍然留在 `cr.ui.browser`。这让 file action 的知识分散：诊断命令要从 browser 里取 open source，同时从 file action module 取 copy/reveal source。

为了让这个终端 workbench 后续更容易扩展 editor 行为、配置诊断和跨语言迁移，需要把 open/editor handoff 收进同一个 file action module。

## What Changes

- 将 open/editor command source resolution、template expansion、platform fallback 和 subprocess launch 移到 `cr.ui.file_actions`。
- `cr.ui.browser` 继续负责 selected-file context：选择当前 changed file、计算 first changed line、展示 browser message/status。
- `file actions` 诊断继续显示 open/copy/reveal 三类来源。
- `open` 命令的用户行为、配置优先级和失败提示保持不变。

## Capabilities

### Modified Capabilities

- `browser-file-actions`: file actions module 统一拥有 open/copy/reveal 的 platform details。
- `browser-file-action-diagnostics`: 诊断从统一 file action source objects 读取 open/copy/reveal 来源。

## Impact

- Touches `src/cr/ui/file_actions.py` to add editor/open ownership.
- Touches `src/cr/ui/browser.py` to delegate open execution and diagnostics.
- Updates tests that currently import browser-private open helpers.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
