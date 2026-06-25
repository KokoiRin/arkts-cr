## Design

The browser already stores parsed problem selection in `BrowserState.problem_selected`.
Task Problems uses it for row selection, while Task Output currently ignores it
for actions. This change makes the selection shared by both pages:

- `next problem` / `prev problem` move `problem_selected` across the current
  filtered/sorted visible problem list.
- Task Output actions read the same selected problem as Task Problems.
- Task Output rendering shows a compact `Problem: N/M path:line` header when
  parsed problems exist.
- When changing problem selection from Task Output, the task scroll position is
  nudged toward the selected problem's original output line.

## Boundaries

- `cr.ui.commands` owns command parsing.
- `cr.ui.browser` owns selection changes and action target selection.
- `cr.ui.page_content` owns the compact selected-problem label.
- Existing task problem extraction, filtering, sorting, grouping, and source
  rendering are reused unchanged.

## Validation

- Parser tests cover the new commands.
- BrowserCommandExecutor tests cover Task Output navigation and handoff target
  selection.
- Page content tests cover the selected-problem label.
- Existing Task Problems selection tests remain unchanged.
