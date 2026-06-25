# Design

This follows the existing copy/save handoff split:

- `task_problems.py` already renders the current list Markdown via `problems_handoff_text`.
- `browser.py` chooses the current visible list or selected-file subset and reports user-facing messages.
- `handoff.py` owns default paths and UTF-8 writes.
- `commands.py`, the command catalog, and page help expose the new commands.

Default paths:

```text
.cr/handoff/task-problems.md
.cr/handoff/task-problems-file.md
```

The selected-file command uses the selected problem's path as the file key and only includes problems from the current visible list. This matches `copy file problems`.
