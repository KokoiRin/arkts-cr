# Design: Source File problem stepping

## Behavior

`next problem` and `prev problem` already share `_jump_task_problem`. This change extends that existing navigation helper: after it updates `problem_selected`, if the current page is Source File, it updates the Source File path and line to the newly selected parsed task problem.

The Source File update should behave like opening a fresh source preview, but without pushing a new page-history entry. Repeated `next problem` should keep the user on Source File, and `b` should still return to the original previous page rather than walking through every visited problem source.

## Boundary

The current task output remains the only source of problem facts. The browser does not store problem origin or diagnostics separately. Source File problem stepping reuses `_current_task_problems`, `problem_selected`, and existing Source File state fields.

## Tests

- Source File `next problem` opens the next problem source and keeps back navigation pointed at the original page.
- Source File `prev problem` opens the previous problem source.
- Task Output `next problem` still scrolls task output and does not open Source File.
