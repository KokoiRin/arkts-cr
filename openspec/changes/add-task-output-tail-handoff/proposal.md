## Why

`cr browse` already supports copying or saving the full current task output, but build/test/lint logs are often much longer than the useful failure tail. When Problems parsing is insufficient or the user wants to hand a compact failure snippet to AI, they still need to manually select the last screenful of logs.

## What Changes

- Add `copy task tail [N]` to copy the current task output handoff text limited to the last N captured output lines.
- Add `save task tail [PATH]` to save the same tail handoff text, defaulting to `.cr/handoff/task-output-tail.md`.
- Default tail size is 40 lines when N is omitted.
- Preserve current task lifecycle, captured output storage, task history, Problems parsing, and workspace persistence.

## Capabilities

### New Capabilities
- `task-output-tail-handoff`: copy or save a compact current-task log tail for AI/reviewer handoff.

## Impact

- Touches `cr.ui.tasks` for pure tail handoff text formatting.
- Touches command parsing/catalog/help and Browser Action Execution for copy/save routing.
- Touches `cr.ui.handoff` only for the default tail save path.
- Does not add dependencies or change task process management.
