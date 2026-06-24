## Context

当前 selected-file action 逻辑散在两个层面：

- `BrowserCommandExecutor` 分支直接读取 `state.visible_changes[state.selected]`，调用 `git.first_changed_line`、`file_actions.copy_text`、`file_actions.reveal_path`、`_copy_prompt_handoff` 等 helper。
- browser helper 函数直接处理 notes、prompt handoff file selection、review data build、workspace sync 和 file-line cache invalidation。

这些行为都围绕“当前 Review Scope / Changed Files 中的 selected file”展开。它们不是 command parsing，不是 terminal rendering，也不是 platform subprocess details。

This is an in-process deepening. The useful seam is:

```text
BrowserCommandExecutor -> Selected File Actions -> user-facing message
```

## Goals / Non-Goals

**Goals:**

- 新增 `cr.ui.selected_file_actions`，作为 selected-file action workflow 的 implementation owner。
- 保留 `browser.py` 旧 helper wrappers，降低测试和调用点迁移成本。
- 让 executor 分支表达“执行哪个 selected-file action”，而不是重新知道 path/line/note/prompt 细节。
- 保持 note state sync、file-line cache clear、prompt handoff review-note filtering 和 empty-state messages 不变。

**Non-Goals:**

- 不改变 command parser、command catalog、command palette 或 key aliases。
- 不改变 `cr.ui.file_actions` 的 platform command resolution/subprocess behavior。
- 不改变 `cr.ui.handoff` 的 path resolution/write behavior。
- 不改变 `cr.review.prompt` Markdown structure。
- 不新增新的 file actions。

## Module Interface

`cr.ui.selected_file_actions` should expose focused helpers:

- `open_selected_change(change, args) -> str`
- `copy_selected_path(path, copy_cmd) -> str`
- `copy_selected_anchor(path, args, copy_cmd) -> str`
- `reveal_selected_path(path, reveal_cmd) -> str`
- `set_selected_review_note(state, note) -> str`
- `copy_prompt_handoff(state, args, selected_only) -> str`
- `save_prompt_handoff(state, args, requested_path, selected_only) -> str`
- `prompt_handoff_text(state, args, selected_only) -> tuple[str, int] | None`

The module may use the live `BrowserState` shape for now. A future typed protocol can be introduced if another implementation language or UI framework needs a narrower interface.

## Behavior Preservation

Extraction must preserve:

- empty selected-file messages such as `No changed file to copy.`
- copy path / anchor message text and clipboard fallback behavior
- open/reveal message text and source-aware failure behavior
- note set/clear messages, workspace sync, and file-line cache invalidation
- prompt copy/save selected-only and scope-wide behavior, including review-note filtering
- prompt save default paths and requested path handling through `cr.ui.handoff`
- executor redraw behavior and raw-key status placement

## Risks / Trade-offs

- **Risk:** the new module reads live `BrowserState`, so its interface is not perfectly narrow.
  **Mitigation:** this keeps the first extraction behavior-preserving; state protocol narrowing can come after the action workflow is localized.

- **Risk:** tests currently patch `cr.ui.browser.file_actions.copy_text`.
  **Mitigation:** keep browser wrappers for existing tests and add new module tests; if needed, leave browser imports patchable during this compatibility phase.

- **Risk:** prompt handoff crosses `cr.review`, `cr.ui.handoff`, and browser state.
  **Mitigation:** the selected-file module owns selection/filtering workflow only; rendering and file writes remain in their existing modules.
