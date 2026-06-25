# Design: Source File copy problem

## Behavior

`copy problem` already maps to the selected task problem. This change specializes the Source File page: it reuses the same exact-match rule as the Source File problem header. The command copies only when the selected parsed task problem has the same path and line as the current Source File target.

When Source File has no matching selected problem, the command does not copy stale diagnostics and instead reports a clear empty state.

## Boundary

The task output remains the source of problem facts. The implementation should share matching logic with the Source File problem header rather than introducing new state.

## Tests

- Source File `copy problem` copies the matching current diagnostic.
- Source File `copy problem` does not copy when the current source target no longer matches the selected problem.
- Task Problems `copy problem` still copies the selected visible problem.
