# Design

## Behavior

`view problem diff` reuses `_current_task_problem_for_action`, so Task Output selected-problem behavior and Task Problems filtering/sorting/grouping remain consistent with `view problem` and `copy problem context`.

After resolving a problem:

1. Find a changed file with the same path in the current visible list.
2. If a user file filter hides it, fall back to the full current review scope, clear file-list filters, and select the matching changed file.
3. Open File Detail through `BrowserNavigation.open_file_detail`.
4. Render/cached File Detail lines for that file and set `file_scroll` to the rendered row whose new-file line matches the problem line when possible.

## Boundaries

The navigation command lives in the browser command-action layer. The row lookup lives in `file_detail_navigation`, which already owns File Detail rendered-line navigation rules.

## Validation

- Command parsing recognizes `view problem diff`.
- Task Problems `view problem diff` opens the matching changed file and scrolls to the matching rendered line.
- Task Output `view problem diff` uses the selected output problem.
- Missing changed file reports a clear message and does not navigate.
