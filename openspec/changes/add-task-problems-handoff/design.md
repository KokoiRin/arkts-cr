## Context

Task Problems is intentionally a lightweight UI projection over current task output. It owns file anchor extraction, while Browser Action Execution owns selection and editor/copy side effects.

## Goals / Non-Goals

**Goals:**

- `copy problem` copies the selected problem from Task Problems Page.
- `copy problems` copies every currently extracted problem.
- Copied text includes repo-relative location and source output summary.
- Empty states report a message and do not launch the clipboard command.
- Copy failures reuse the configured clipboard command error path.

**Non-Goals:**

- No severity, category, tool, or error-code parsing.
- No historical task record copying.
- No persistence or `save problems` command.
- No mutation of current page, selection, scroll, task state, or review scope.

## Decisions

1. **Formatting belongs in `cr.ui.task_problems`.**
   - Choice: add selected/all handoff text helpers next to extraction.
   - Reason: callers should not re-encode problem location formatting or list shape.

2. **Copy side effects stay in Browser Action Execution.**
   - Choice: `BrowserCommandExecutor` calls a small browser helper that gets current problems and uses `file_actions.copy_text`.
   - Reason: clipboard execution is already a UI-edge concern, not extraction behavior.

3. **No save command yet.**
   - Choice: ship clipboard handoff only.
   - Reason: `copy task` already covers durable full log context through `save task`; problems save can wait until real usage shows a need.

## Risks / Trade-offs

- **All-problems copy can duplicate entries**: duplicates are kept because duplicate log anchors often carry useful context or order.
- **No severity labels**: this keeps the module honest until real tool output examples justify parser-specific enrichment.
