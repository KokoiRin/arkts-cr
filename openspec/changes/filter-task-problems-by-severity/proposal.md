## Why

Task Problems now shows severity/code/message facts, but large task outputs can still mix many warnings with the few errors that block the current loop. IDE Problems panels usually let users focus on a severity class. The TUI should support that same high-frequency scan path without changing task output order or introducing a full diagnostics subsystem.

## What Changes

- Add Task Problems severity filters for `error`, `warning`, `info`, and `note`.
- Add commands for applying and clearing the filter.
- Apply the active filter consistently to Problems rendering, movement, open, source preview, and copy actions.
- Show the active filter in the Problems page header and empty state.

## Scope

- `task-problems-filter`: page-local severity filtering of current task problems.
- `browser-command-dispatch`: command parsing and execution for setting/clearing the filter.

## Non-Goals

- No severity sorting.
- No text query filtering.
- No task history search.
- No diagnostics persistence.
- No tool-specific parser registry.
