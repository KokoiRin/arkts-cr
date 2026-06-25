## Behavior
`source mark` records `source_file_line` as `source_mark_line` when the browser
is on Source File Page. `source select to` requires an active mark and then sets
`source_selection_start` / `source_selection_end` to the sorted mark/current
line pair. `source clear mark` resets only the mark.

The mark is page-local and restored through in-session page history, matching
the existing selection, context radius, source find, and scroll behavior.
Opening a different Source File Page clears the mark.

## Module Boundaries
- `cr.ui.commands` parses the new command literals into stable actions.
- `cr.ui.navigation` snapshots and restores the page-local mark.
- `cr.ui.browser` executes mark/select/clear and reports status feedback.
- `cr.ui.page_content` and `cr.ui.command_catalog` expose discoverable Chinese
  hints for the commands.

No source parsing, syntax-aware selection, persistence, mouse support, or
editing is added.
