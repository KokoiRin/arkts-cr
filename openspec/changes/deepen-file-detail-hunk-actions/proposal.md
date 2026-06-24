## Why

`BrowserCommandExecutor` still owns the workflow for `open hunk` and
`copy hunk`, even though nearby selected-file operations already live in
`cr.ui.selected_file_actions`.

As File Detail becomes more IDE-like, leaving each hunk action in
`browser.py` makes the command executor grow with product behavior and weakens
the module shape needed for future larger UI/runtime rewrites.

## What Changes

- Move File Detail hunk open/copy workflow into `cr.ui.selected_file_actions`.
- Keep rendered hunk discovery in `cr.ui.file_detail_navigation`.
- Keep browser page checks, line cache retrieval, status placement, and redraw
  decisions in `browser.py`.
- Preserve all user-visible `open hunk` and `copy hunk` behavior.

## Impact

- `BrowserCommandExecutor` remains a thin router for parsed actions.
- File Detail hunk actions become testable through a selected-file action
  interface.
- No command syntax, clipboard/editor configuration, or rendered text changes.
