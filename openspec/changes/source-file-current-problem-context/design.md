# Design

## Behavior

Source File already has `_source_file_task_problem`, the same exact-match helper used by the `problem:` header and single-problem handoff. `copy problem context` should reuse that helper.

For `state.page == SOURCE_FILE`:

1. Build the existing `ProblemContextTarget` from `source_file_path`, `source_file_line`, context lines, and source selection.
2. If `_source_file_task_problem(state)` returns a problem, populate `problem_text` with existing single-problem handoff text.
3. Populate `task_output_text` with the existing task output excerpt helper.
4. If no exact match exists, keep problem/task output fields empty.

## Boundaries

- TUI command handling chooses the current problem because it owns Source File state and selected task problem state.
- Markdown assembly stays in `problem_context.py`.
- Task Output and Task Problems behavior stays unchanged.
- File Detail behavior stays unchanged.

## User-facing messages

No new command or success message is required. The visible behavior is that Source File `copy/save problem context` includes `## Problem` and `## Task Output` sections when the current source line matches the displayed task problem.
