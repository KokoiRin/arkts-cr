## Why

Task Problems Page can now collect current build/test/lint file anchors and open them in the editor. The next IDE-like loop is handoff: when a build fails, users often need to paste one failing location or the whole current Problems list into AI/chat without copying raw terminal output manually.

## What Changes

- Add `copy problem` for copying the selected Task Problems entry.
- Add `copy problems` for copying all current Task Problems entries.
- Reuse existing copy command configuration and failure messages.
- Keep the current Task Problems page, selection, scroll, Review Scope, and task state unchanged.
- Do not add severity parsing, error-code parsing, task history search, persistence, or save-to-file behavior.

## Capabilities

### New Capabilities

- `task-problems-handoff`: copy selected or all current Task Problems entries as compact text.

### Modified Capabilities

- `task-problems-page`: exposes copy actions for current-task problem anchors.
- `browser-command-dispatch`: parses `copy problem` and `copy problems`.

## Impact

- Extends `cr.ui.task_problems` with formatting helpers.
- Extends `cr.ui.commands`, `cr.ui.command_catalog`, `cr.ui.page_content`, and `cr.ui.browser`.
- Reuses `cr.ui.file_actions.copy_text`.
- Does not touch task runtime lifecycle, Git review facts, workspace persistence, or editor open behavior.
