## Behavior
`copy file problems` is available from Task Problems and uses the same visible
problem list as movement, Enter/open, `copy problem`, and `copy problems`.

The selected problem's `path` becomes the file key. The command filters the
visible problems to that path, renders them with the existing task-problems
handoff Markdown, copies through the configured copy command, and reports how
many problems were copied for that file.

## Module Boundaries
- `cr.ui.commands` parses the command literal.
- `cr.ui.browser` owns selected-problem lookup and clipboard side effects.
- `cr.ui.task_problems` continues to own problem handoff Markdown.
- `cr.ui.page_content` and `cr.ui.command_catalog` expose discoverable text.

## Non-goals
- No external quick-fix commands.
- No group collapse/expand state.
- No new task-problem persistence or history.
- No tool-specific diagnostic parser changes.
