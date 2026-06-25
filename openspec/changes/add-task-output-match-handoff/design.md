# Design

The command stays in the existing Task Output handoff family:

- `commands.py` maps `copy task match` and `save task match [PATH]` to stable browser actions.
- `tasks.py` renders the Markdown handoff text from `TaskState`, current `task_scroll`, and `task_find_text`.
- `browser.py` owns user-facing preconditions: a task must exist, task output must be non-empty, and `find TEXT` must have been used first.
- `handoff.py` owns default path resolution and UTF-8 file writes.

The focused line is the current Task Output scroll position. Existing `find`, `next match`, and `prev match` already move that position, while manual scrolling can intentionally shift the copied focus.
