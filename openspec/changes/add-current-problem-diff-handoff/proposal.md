## Why

`view problem diff` helps jump from a build/test problem into the changed-file diff, and `copy problem context` packages a full AI handoff. There is still a smaller handoff shape missing: copy or save only the changed-file diff for the current problem without navigating away or including source and task-output context.

## What Changes

- Add `copy problem diff` for the current task problem.
- Add `save problem diff [PATH]`, defaulting to `.cr/handoff/problem-diff.md`.
- Support Task Output, Task Problems, and exact-match Source File current problems.
- Reuse the existing file diff snippet renderer and current review scope.
- Update Chinese help, command discovery, README, and P0 history.

## Non-Goals

- No synthetic diff for files outside the current review scope.
- No source/task-output packaging; users should keep using `copy problem context`.
- No new diagnostic parser, quick fix, editing, task history, or persisted problem model.
