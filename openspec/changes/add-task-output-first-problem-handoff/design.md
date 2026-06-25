# Design

## Command Surface

The existing commands keep their names:

- `view problem`
- `copy problem context`
- `save problem context [PATH]`

When the current page is `BrowserPage.TASK_OUTPUT`, these commands act on the
first visible parsed problem from current task output.

## Selection Rule

Task Output has no problem row selection. To keep the model predictable:

1. Extract task problems with the existing `cr.ui.task_problems` parser.
2. Apply existing `state.problem_filter`, `state.problem_query`, and
   `state.problem_sort`.
3. Choose index `0` from that visible list.
4. Do not mutate `state.problem_selected`.

Task Problems continues to use `state.problem_selected`.

## Errors

- If no task exists or no visible problem can be parsed, keep the current empty
  messages:
  - `No task problem to view.`
  - `No problem context to copy.`
  - `No problem context to save.`
- Source read and save errors continue to surface through the existing helpers.

## Boundaries

The task-problems module remains the only source of parsed diagnostic facts.
Browser execution chooses the page-specific target; problem-context assembly
continues to live in the existing handoff path.
