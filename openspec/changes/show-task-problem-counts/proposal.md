## Why

Task Problems now has severity labels and severity filters, but users still have to visually scan rows to know how many errors, warnings, info, or notes are in the current view. IDE Problems panels usually expose these counts immediately. The TUI should do the same without changing ordering or adding a broader diagnostics subsystem.

## What Changes

- Add a compact severity count label for visible Task Problems.
- Render the count label in the Task Problems header.
- Keep filtering, movement, open, and copy behavior unchanged.

## Scope

- `task-problems-counts`: count visible Task Problems by severity for display.

## Non-Goals

- No severity sorting.
- No total-vs-filtered aggregate state.
- No persistent diagnostics.
- No new commands.
- No tool-specific parser registry.
