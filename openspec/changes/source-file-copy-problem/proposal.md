# Change: Source File copy problem

## Why

Source File can show the current task problem in its header, but users still need a quick way to copy just that diagnostic while reading source. The existing `copy problem context` is larger and includes source/diff context; sometimes the smallest useful handoff is only the current diagnostic.

## What Changes

- On Source File, `copy problem` copies the task problem that exactly matches the current source path and line.
- If the selected task problem no longer matches the current source target, Source File reports that there is no current source problem to copy.
- Task Output and Task Problems keep their existing selected-problem copy behavior.

## Non-Goals

- No diagnostics persistence.
- No new problem-origin state.
- No batch copy.
- No quick fixes, source editing, or language-service integration.
