## Design

Problem Context generation stays split across two layers:

- `cr.ui.browser` chooses the active context target and gathers source, diff,
  and task-output facts from current browser state.
- `cr.ui.problem_context` only assembles Markdown text.

For Task Output and Task Problems pages, the selected `TaskProblem.output_line`
is the authoritative anchor back into `state.task.lines`. The browser formats a
small plain-text excerpt around that line and passes it into the Markdown
composer. Source File Page contexts pass no task output excerpt.

## Boundaries

- The excerpt is display/handoff data only; it does not affect task problem
  extraction, sorting, filtering, grouping, or page selection.
- The browser owns ANSI stripping through the existing task-output text helper.
- The Markdown composer remains pure and testable.
- The initial excerpt size is intentionally fixed and small to avoid turning
  Problem Context into a log export feature.

## Validation

- BrowserCommandExecutor tests cover copy/save from Task Problems and Task
  Output.
- Source File Page tests confirm it still omits task output.
- Focused unit tests exercise Markdown composition.
