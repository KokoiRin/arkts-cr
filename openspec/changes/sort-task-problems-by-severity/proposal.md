## Why

Task Problems now exposes severity labels, filters, and visible counts. The next IDE-like operation is optional severity sorting so users can group blocking errors before warnings and unknown anchors. This should be opt-in because task-output order is still valuable for understanding build logs.

## What Changes

- Add an optional Task Problems sort mode: output order or severity order.
- Add commands to switch sort modes.
- Apply the active sort consistently to rendering, movement, open, source preview, and copy actions.
- Show the active severity sort in the Problems header.

## Scope

- `task-problems-sort`: page-local optional sorting of current visible Task Problems.
- `browser-command-dispatch`: command parsing and execution for sort mode changes.

## Non-Goals

- No default sorting.
- No text query filtering.
- No persistent diagnostics.
- No tool-specific parser registry.
- No user-configurable severity ordering.
