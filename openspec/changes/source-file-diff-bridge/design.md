# Design: Source File diff bridge

## Behavior

`view diff` and `view problem diff` on Source File use the current `source_file_path` and `source_file_line` as the source anchor. If that path is present in the active review scope, the browser switches to File Detail for that changed file. If the rendered diff contains a row for the source line, File Detail scrolls to that row; otherwise it opens the file at the existing/default scroll position and reports that the line is not visible in the diff.

Task Output and Task Problems keep using the selected parsed task problem, because those pages already have problem selection semantics.

## Boundary

This is a TUI navigation bridge only. It reuses `_select_changed_file_for_problem_diff`, `_cached_file_lines`, and `file_detail_navigation.new_line_position`. It does not add a problem-origin field to `BrowserState`, because the Source File current path/line is already the stable fact needed for navigation.

## Tests

- Source File `view diff` opens File Detail for the current source path and scrolls to the matching rendered new-file line.
- Source File reports a clear no-diff message when the source path is not in the current review scope.
- Parser, command catalog, and page help expose `view diff` without changing existing `view problem diff` behavior.
