## Why

`cr browse` 已经支持 per-file review notes，也支持 `copy prompt` / `copy prompt file` 把当前 review context 复制给 AI 或聊天。但现在 handoff 只包含 diff/risk/purpose/focus 等自动事实，不包含用户刚在浏览器里写下的人工判断。实际 review 时，这些 notes 往往就是最该带给 AI 的上下文：疑点、待确认点、owner 问题、回归风险。

为了让 `cr` 更像一个替代 IDE 的 review workbench，prompt handoff 应该保留这部分人工上下文，而且应该通过 `cr.review` 的 prompt renderer 表达，而不是让 browser 自己拼 Markdown。

## What Changes

- `cr.review.data.build_review_data` 支持可选 `review_notes`，并把匹配文件的 note 放进对应 file data。
- `cr.review.prompt.render_prompt_handoff` 在文件 summary 和 detail 中渲染 `review note` 行。
- `copy prompt` / `copy prompt file` 传入当前 browser workspace 的 `review_notes`。
- 没有 note 的 prompt 输出保持现有格式。
- `cr review --prompt` 不引入持久化 notes 读取，仍按现有 CLI 输入生成 prompt。

## Capabilities

### Modified Capabilities

- `browser-prompt-copy`: browser prompt copy includes matching review notes from the current Review Workspace.
- `review-session-handoff`: prompt renderer owns review note formatting when notes are supplied in review data.

## Impact

- Touches `src/cr/review/data.py` and `src/cr/review/prompt.py` for optional review note data and rendering.
- Touches `src/cr/ui/browser.py` to pass current workspace notes into prompt handoff.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
- Adds focused tests for prompt rendering, review data assembly, and browser prompt copy handoff.
