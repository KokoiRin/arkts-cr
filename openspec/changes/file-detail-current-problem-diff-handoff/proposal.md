# File Detail current problem diff handoff

## Why

File Detail now lets users copy or save the task problem for the current diff row. The adjacent `copy problem diff` and `save problem diff` commands still use the globally selected task problem outside Source File, so they can export another file's diff while the user is reading a specific changed row.

## What changes

- In File Detail, `copy problem diff` targets the task problem that exactly matches the current rendered new-file line and changed file.
- In File Detail, `save problem diff [PATH]` saves the same current-row problem diff.
- If the current row has no new-file line or no matching task problem, refuse without falling back to the global selected problem.
- Task Output, Task Problems, and Source File keep their existing behavior.

## Non-goals

- No synthetic diffs for unchanged files.
- No diagnostics persistence.
- No parser or language-service integration.
- No source editing, quick fixes, or cross-file dependency collection.
