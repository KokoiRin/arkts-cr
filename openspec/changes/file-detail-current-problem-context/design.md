# Design

## Behavior

File Detail already resolves the current changed file and rendered new-file line for problem context handoff. This change enriches that target when a visible parsed task problem exactly matches the same path and line.

For `state.page == FILE_DETAIL`:

1. Resolve `(path, line)` with the existing File Detail source-target helper.
2. Look for a visible task problem whose `path` and `line` exactly match.
3. If found, populate `ProblemContextTarget.problem_text` and `task_output_text` using the same helpers as Task Output and Task Problems.
4. If not found, return the same source + diff target as before.

## Boundaries

- The current-row matching stays in TUI command handling because it depends on rendered File Detail scroll state.
- Markdown assembly stays in `problem_context.py`.
- Problem parsing and task output excerpt logic stay unchanged.
- Task Output, Task Problems, and Source File context behavior stays unchanged.

## User-facing messages

No new command or success message is required. The visible behavior is the presence of `## Problem` and `## Task Output` sections in the copied or saved context when the current File Detail row matches a task problem.
