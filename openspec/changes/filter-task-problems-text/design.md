## Design

Task Problems already uses page-local `problem_filter` for severity and `problem_sort` for ordering. Text filtering should follow the same model:

- `BrowserState.problem_query` stores the active query.
- `BrowserNavigation` snapshots and restores it with Task Problems page history.
- `cr.ui.task_problems` owns pure query matching.
- Browser Action Execution parses and applies `problems find TEXT` / `problems clear find`.
- `_current_task_problems` applies severity filter, then query filter, then sort.

## Behavior

Query matching is case-insensitive plain text. It matches:

- path and `path:line[:column]` location
- summary
- severity
- diagnostic code
- diagnostic message

An empty or whitespace query clears the query. Query filtering composes with severity filtering and severity sort. The header shows the active query so the user can see why a list is narrowed.

## Boundaries

This is not a full diagnostics search system. It only filters the current task's extracted Problems list and does not search raw task output history, source files, or build-tool-specific metadata.
