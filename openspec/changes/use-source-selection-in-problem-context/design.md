## Design

Problem Context generation currently asks the browser for a
`ProblemContextTarget` and then always renders source with
`source_context_markdown()`. This change lets Source File targets optionally
carry a selected source range.

Behavior:

- On Source File Page with an active `source_selection_start/end`, Problem
  Context renders `source_range_markdown()` for that selected range.
- The current `source_file_line` remains the target marker inside the selected
  range when possible.
- On Source File Page without a selection, existing context-radius rendering is
  unchanged.
- Task Output and Task Problems keep using the selected/visible task problem
  target and line-context source snippet.

## Boundaries

- Selection interpretation stays in `cr.ui.browser`.
- Markdown formatting continues to use existing `cr.ui.source_file` helpers.
- `cr.ui.problem_context` remains a pure Markdown composer.
- No new command syntax is added.

## Validation

- BrowserCommandExecutor tests cover selected Source File copy/save problem
  context.
- Existing Source File no-selection context tests continue to prove current
  context-radius behavior.
- Existing Task Output/Task Problems problem context tests continue to prove
  those pages are unchanged.
