## Why

`open`、`copy path`、`copy anchor` 和 `reveal` 已经让 `cr browse` 更像一个小 IDE，但当这些动作失败时，用户很难判断到底是 CLI 参数、环境变量、平台 fallback，还是缺少系统命令导致的。一个 terminal workbench 应该能解释自己准备调用什么，而不是只给一句失败。

## What Changes

- 新增 `file actions` 浏览器命令，显示 open/copy/reveal 的解析来源和命令。
- copy/reveal 缺少命令或启动失败时，错误消息带上解析来源。
- open 缺少命令或启动失败时，错误消息带上解析来源。
- 保持成功路径简洁，不在普通成功消息里输出完整命令。

## Capabilities

### New Capabilities

- `browser-file-action-diagnostics`: 定义浏览器内文件动作来源诊断。

### Modified Capabilities

- `browser-file-action-configuration`: copy/reveal 配置保持不变，但失败消息和诊断会解释来源。
- `browser-editor-handoff`: open 配置保持不变，但失败消息和诊断会解释来源。

## Impact

- Touches `src/cr/ui/file_actions.py` for copy/reveal source resolution.
- Touches `src/cr/ui/browser.py` for open source diagnostics and command execution.
- Touches `src/cr/ui/commands.py` for command parsing.
- Updates README, CONTEXT, design, navigation roadmap, and P0 docs.
- Adds focused tests for source resolution, diagnostics command, and failure messages.
