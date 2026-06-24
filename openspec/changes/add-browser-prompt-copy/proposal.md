## Why

`cr review --prompt` 已经能生成适合贴给 AI 或聊天的 Markdown review handoff，但在 `cr browse` 里用户还要退出当前浏览上下文、重新拼命令或复制终端输出。作为 terminal workbench，浏览器应该能直接把当前 review scope 或当前文件的上下文复制出去，让 AI review / 代码讨论成为一个原地动作。

## What Changes

- 新增 `copy prompt` 命令，复制当前 Review Scope 的 prompt-ready Markdown。
- 新增 `copy prompt file` 命令，复制当前选中文件的 prompt-ready Markdown。
- 复制内容复用 `cr.review.data.build_review_data` 和 `cr.review.prompt.render_prompt_handoff`，避免浏览器维护另一套 prompt 格式。
- 没有可复制变更时显示明确空状态，不调用剪贴板命令。
- 命令不改变当前 page、selection、scope、filter、task 或 review notes。

## Capabilities

### New Capabilities

- `browser-prompt-copy`: 定义 interactive browser 中复制 review prompt handoff 的能力。

### Modified Capabilities

- `browser-file-actions`: prompt copy 使用现有 clipboard command resolution，不新增复制配置。
- `review-session-handoff`: 浏览器复用已有 prompt handoff renderer，而不是分叉 Markdown 格式。

## Impact

- Touches `src/cr/ui/commands.py` for `copy prompt` / `copy prompt file` command parsing.
- Touches `src/cr/ui/browser.py` for command execution and command catalog visibility.
- Reuses `cr.review.data.build_review_data`, `cr.review.prompt.render_prompt_handoff`, and `cr.ui.file_actions.copy_text`.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
- Adds focused tests for parsing, scope prompt copy, file prompt copy, empty state, raw-key feedback, and command catalog discoverability.
