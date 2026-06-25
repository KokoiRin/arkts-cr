# Design

## Behavior

`copy problem` and `save problem` already have page-specific behavior for Source File: they only operate when the selected task problem exactly matches the current source path and line. File Detail should use the same safety principle, but derive the target from the currently rendered diff row.

When `state.page == FILE_DETAIL`:

1. Resolve the current changed file and current new-file line with the existing File Detail source-target helper.
2. Extract current visible task problems with existing filtering/sorting rules.
3. Find the first problem whose `path` and `line` exactly match the current changed file and new-file line.
4. Copy or save that single problem using the existing single-problem handoff text.

## Boundaries

- TUI command handling chooses the target because the concept of "current rendered row" is UI state.
- Problem parsing, formatting, and save/copy boundaries stay unchanged.
- Task Output and Task Problems keep their selected-problem behavior.
- Source File keeps its exact-match current source behavior.

## User-facing messages

- Copy success: `Copied file problem <path>:<line>.`
- Save success: `Saved file problem <path>:<line> to <display path>.`
- No new-file line: existing `No current new-file line in File Detail.`
- No matching problem: `No current file problem to copy.` or `No current file problem to save.`
