# Design

## Behavior

`copy problem diff` and `save problem diff` already delegate to the existing diff snippet renderer after choosing a task problem. This change only adjusts problem selection while the browser is on File Detail.

When `state.page == FILE_DETAIL`:

1. Resolve the current changed file and current new-file line with the existing File Detail source-target helper.
2. Find the visible task problem whose `path` and `line` exactly match that target.
3. Render the current review-scope diff for that problem's file using the existing diff snippet path.
4. Copy or save the rendered diff with the existing handoff boundaries.

## Boundaries

- The current-row decision stays in TUI command handling because it depends on rendered File Detail scroll state.
- Problem parsing, sorting/filtering, diff snippet rendering, and handoff persistence stay unchanged.
- Task Output and Task Problems continue using the selected task problem.
- Source File continues using its exact source path/line problem match.

## User-facing messages

- Copy success: existing `Copied problem diff <path>:<line>.`
- Save success: existing `Saved problem diff <path>:<line> to <display path>.`
- No matching File Detail problem: `No current file problem diff to copy.` or `No current file problem diff to save.`
- No changed file diff: existing `No diff for problem <path>:<line> in current review scope.`
