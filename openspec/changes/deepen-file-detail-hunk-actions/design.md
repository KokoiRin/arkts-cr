## Design

Add two selected-file action helpers:

- `open_selected_hunk(change, lines, current_scroll, args, ...) -> str`
- `copy_selected_hunk(change, lines, current_scroll, args, ...) -> str`

The helpers receive the already selected `FileChange` and already rendered File
Detail `lines`. This keeps them free of browser page state, visible-list
selection, and render-cache ownership.

## Module Boundaries

- `cr.ui.file_detail_navigation` owns rendered hunk detection, active hunk
  extraction, and new-file line resolution.
- `cr.ui.selected_file_actions` owns selected-file workflow messages and
  platform action invocation for open/copy hunk.
- `cr.ui.file_actions` owns the subprocess/platform adapters for editor and
  clipboard.
- `browser.py` owns page validation, selection clamping, cached File Detail line
  retrieval, Browser Frame status placement, and redraw control.

## Non-Goals

- Do not change `open hunk` or `copy hunk` command syntax.
- Do not change the copied hunk Markdown format.
- Do not add new hunk navigation behavior.
- Do not move File Detail rendering or cache ownership out of browser/page
  content in this change.

## Verification

- Unit tests cover selected-file hunk open/copy helpers directly.
- Existing executor tests continue to prove browser state preservation and
  status feedback.
- OpenSpec strict validation, compile checks, diff checks, and full unit tests
  must pass.
