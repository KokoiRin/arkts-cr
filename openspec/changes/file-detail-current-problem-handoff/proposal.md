# File Detail current problem handoff

## Why

File Detail is where users read a changed file after build/test/lint failures. `copy problem` and `save problem` still behave like Task Problems outside Source File: they use the global selected task problem. That can export a different file's diagnostic while the user is reading a specific diff row.

## What changes

- In File Detail, `copy problem` targets the task problem that exactly matches the current rendered new-file line and current changed file.
- In File Detail, `save problem [PATH]` saves that same current-row problem.
- If the current File Detail row has no new-file line, reuse the existing current-line refusal.
- If the current row has no matching task problem, refuse without falling back to the global selected problem.

## Non-goals

- No diagnostics persistence.
- No parser or language-service integration.
- No synthetic mapping for deleted-only rows.
- No source editing, quick fixes, or multi-problem batch export changes.
