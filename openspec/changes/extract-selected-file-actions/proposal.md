## Why

`cr browse` 的命令执行层已经从字符串解析中解耦，但 `BrowserCommandExecutor` 仍直接拥有一组 selected-file side effects：open、copy path、copy anchor、reveal、per-file note、copy/save prompt file，以及 scope-level prompt handoff。它们共同依赖当前 visible changes、selected index、first changed line、review notes、prompt handoff Markdown、clipboard/editor/file-browser helpers、file-line cache invalidation 和 workspace sync。

这组知识不是通用 command execution，也不是平台 subprocess 细节。继续留在 `browser.py` 会让每个新 IDE-like 文件动作都继续扩大 executor 分支。为了后续加入更多常用 IDE 操作，需要把 selected-file action workflow 加深成独立 UI module。

## What Changes

- 新增 `cr.ui.selected_file_actions` module，拥有 selected-file action workflow：open selected file、copy selected path、copy selected anchor、reveal selected file、set/clear selected-file note、copy/save prompt handoff、prompt handoff text selection。
- `src/cr/ui/browser.py` 保留现有 `_open_change`、`_set_selected_review_note`、`_copy_prompt_handoff`、`_save_prompt_handoff`、`_prompt_handoff_text` wrappers，但实现委托给新 module。
- `BrowserCommandExecutor` 继续拥有 parsed command action routing 和 UI feedback placement；新 module 返回 user-facing message。
- `cr.ui.file_actions` 继续拥有 platform command templates/subprocesses；`cr.ui.handoff` 继续拥有 handoff file path/write behavior；`cr.review.prompt` 继续拥有 Markdown rendering。
- 不改变用户可见命令、消息、clipboard/open/reveal behavior、prompt file defaults、review note persistence、file cache invalidation 或 redraw behavior。

## Capabilities

### New Capabilities

- `selected-file-actions-module`: 定义 selected-file action workflow 的 ownership 和行为保持要求。

### Modified Capabilities

- `browser-action-execution`: action executor routes parsed commands but no longer owns selected-file workflow implementation details.
- `browser-file-actions`: platform file action helpers remain in `cr.ui.file_actions`, while selected-file workflow moves to the new module.

## Impact

- Adds `src/cr/ui/selected_file_actions.py`.
- Touches `src/cr/ui/browser.py` to delegate selected-file action helpers and executor branches.
- Adds focused module-level tests for selected-file action messages, note state/cache invalidation, and prompt handoff selection.
- Updates CONTEXT, design, navigation roadmap, and P0 notes.
