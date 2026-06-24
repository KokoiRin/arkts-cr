## Why

File Detail now supports hunk-to-hunk navigation, but `open` still jumps to the
file's first changed line. In an IDE-like review workflow, once the user has
scrolled or jumped to a specific hunk, editor handoff should open that hunk
instead of forcing another search in the editor.

This change adds `open hunk` for File Detail.

## What Changes

- Add command parsing and command catalog entry for `open hunk`.
- Extend File Detail navigation rules to resolve the current hunk's new-file
  start line from rendered hunk headers.
- Execute `open hunk` through the existing editor handoff path and configured
  open command.
- Preserve Review Scope, selected file, filters, notes, progress, and task
  state.
- Surface clear feedback outside File Detail, when no changed file is selected,
  when the current file has no hunk, and when editor handoff fails.

## Capabilities

### New Capabilities

- `file-detail-open-hunk`: users can open the current File Detail hunk in their
  editor.

### Modified Capabilities

无。

## Impact

- Updates `src/cr/ui/file_detail_navigation.py` to resolve hunk anchors.
- Updates browser command parsing, command catalog, executor routing, README,
  context, and P0 docs.
- Adds focused hunk-anchor, parser, catalog, and executor tests.
