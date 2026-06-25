## Behavior

`save problem [PATH]` saves the same Markdown produced by `copy problem`.

Selection rules:

- On Task Problems, save the selected visible problem.
- On Task Output, save the currently selected parsed output problem.
- On Source File, save only when the current source path and target line exactly match the selected parsed task problem, matching the `problem:` header and `copy problem` stale-protection behavior.

When no path is supplied, the command writes `.cr/handoff/task-problem.md`.

## Boundaries

The command parser owns the new action name. `browser.py` chooses the current problem from browser state. `task_problems.py` continues to render diagnostic Markdown. `handoff.py` owns only path resolution and UTF-8 file writing.

The change intentionally does not introduce a new diagnostic store or page state.
