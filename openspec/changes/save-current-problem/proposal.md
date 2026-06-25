## Why

`copy problem` can hand off one diagnostic, but clipboard-only handoff is brittle in remote terminals and longer review loops. Users need the same focused diagnostic saved as a durable file without expanding into full source/diff context.

## What Changes

- Add `save problem [PATH]` for the currently selected task problem.
- Reuse the same current-problem selection rules as `copy problem`.
- Default to `.cr/handoff/task-problem.md` when no path is supplied.
- Document the command in page help, command catalog, README, and P0 history.

## Non-Goals

- No new diagnostic parser.
- No batch save behavior; `save problems` and `save file problems` already cover lists.
- No source/diff expansion; `save problem context` already covers richer handoff.
- No quick-fix, editing, task history, or diagnostics persistence.
