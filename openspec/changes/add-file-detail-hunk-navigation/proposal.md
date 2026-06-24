## Why

File Detail can already show compact hunks, but large files still require
linear scrolling to move between changed blocks. An IDE-like review workflow
needs a fast way to jump hunk-to-hunk while staying inside the same file.

This change adds `next hunk` and `prev hunk` as File Detail navigation commands.

## What Changes

- Add command parsing and command catalog entries for `next hunk` and
  `prev hunk`.
- Add a small File Detail navigation module that finds rendered diff hunk
  headers and chooses the next/previous scroll position.
- Execute hunk jumps through `BrowserCommandExecutor` without changing Review
  Scope, selected file, filters, review notes, progress, or task state.
- Surface clear status messages when the current file has no hunks, the user is
  already at the first/last hunk, or the command is run outside File Detail.

## Capabilities

### New Capabilities

- `file-detail-hunk-navigation`: users can jump between diff hunks inside the
  selected file detail view.

### Modified Capabilities

无。

## Impact

- Adds `src/cr/ui/file_detail_navigation.py`.
- Updates browser command parsing, command catalog, executor routing, README,
  context, and P0 docs.
- Adds focused navigation, parser, catalog, and executor tests.
