## Demand Card

Implement Source File Page line-range selection.

Expected behavior:

- Input: `source select START END` on Source File Page, where both values are
  positive line numbers.
- Output: page-local selected range, normalized into ascending order and
  clamped to the current file length when copying/rendering.
- Copy behavior: `copy source` copies the selected range when active; otherwise
  it keeps copying the existing target-line context radius.
- Clear behavior: `source clear selection` removes the active range.
- Navigation behavior: opening a new Source File Page clears selection; page
  history restores selection with the rest of the source-page state.

Not doing:

- Editing, syntax expansion, cross-file selection, mouse support, multi-ranges,
  or persisted selection state.

Acceptance:

- Parser/catalog/action-bar expose the commands.
- Source rendering shows selected rows and header range.
- Copy uses selected range when active and old context behavior when inactive.
- Page history restores selected range.

## Design

Source File Page already has page-local state for `source_file_path`,
`source_file_line`, `source_file_scroll`, `source_find_text`, and
`source_context_lines`. Range selection should follow that model:

- `BrowserState.source_selection_start` and `source_selection_end` store the
  active range, with `0` meaning no selection.
- `BrowserNavigation` resets selection on `show_source_file()` and includes it
  in snapshots.
- `cr.ui.source_file` owns pure selected-row facts and selected-source Markdown.
- `Page Content` renders selected rows and a compact `selection: A-B` header.
- `BrowserCommandExecutor` parses and applies `source select START END` and
  `source clear selection`, then routes `copy source` to either selected-range
  or context-radius Markdown.

## Behavior Details

Selection input is plain line numbers, not syntax or rendered-row indices.
Reverse input such as `source select 20 10` normalizes to `10-20`. Copy clamps
the normalized range to file bounds and keeps a target marker if the current
target line sits inside the selected range.

Invalid ranges report a status message and leave the existing selection
unchanged. Empty or unreadable source files follow the existing source-file
error paths.

## Boundaries

This is still a read-only source preview. It should not enter Review Workspace
persistence, task diagnostics, File Detail selection, or editor handoff logic.
