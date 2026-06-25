# Design: Source File problem header

## Behavior

The browser computes a Source File problem label from `_current_task_problems` and `problem_selected`. A label is shown only when the selected problem's path and line equal `source_file_path` and `source_file_line`. That keeps the label accurate after `find`, symbol jumps, or non-problem source navigation.

The label is compact and render-only, for example:

```text
problem: 2/3 ERROR TS2345 Message text
```

If there is no selected problem, no task output, no matching problem, or the current source line differs, Source File renders exactly as before.

## Boundary

This change belongs at the UI presentation boundary. It does not add problem-origin state to `BrowserState`; the task output remains the source of diagnostic truth.

## Tests

- Page rendering includes `problem: ...` when an explicit problem label is provided.
- Browser Source File rendering includes the selected matching task problem label.
- Browser Source File rendering hides the problem label when the current source line does not match the selected problem.
