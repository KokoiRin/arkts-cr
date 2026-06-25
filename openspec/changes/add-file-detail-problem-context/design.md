# Design

## Behavior

When the browser is on File Detail, `copy problem context` and `save problem context` reuse the existing current-row mapping used by `view source` and `copy source`.

If the current rendered row maps to a new-file line, the command builds a `ProblemContextTarget` with:

- `path`: selected changed file path
- `line`: current new-file line
- `context_lines`: current `state.source_context_lines`
- empty problem text and task output text

The existing problem-context renderer then loads source content and appends `_problem_context_diff` for the same changed file.

## Boundaries

The change stays in the UI command-action layer because it is connecting an existing File Detail cursor to an existing handoff renderer. It does not change review data, diff parsing, task problem parsing, or source outline logic.

## Validation

- A File Detail copy test verifies source context, diff context, no task-output section, and page/scroll preservation.
- A File Detail save test verifies the saved bundle uses the current diff row.
- A deleted-only current row test verifies no copy occurs and the user gets the current File Detail no-new-line message.
