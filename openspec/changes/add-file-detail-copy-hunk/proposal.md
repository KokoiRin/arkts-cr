## Why

After hunk navigation and `open hunk`, File Detail can position the user on a
specific changed block. The next common IDE-like workflow is sharing that exact
block with an AI assistant, teammate, or PR comment without copying the whole
file diff.

This change adds `copy hunk` for File Detail.

## What Changes

- Add command parsing and command catalog entry for `copy hunk`.
- Extend File Detail hunk rules to extract the active rendered hunk block.
- Copy a compact Markdown hunk snippet containing the selected file path,
  active hunk anchor, and rendered hunk lines.
- Preserve Review Scope, selected file, filters, notes, progress, and task
  state.
- Surface clear feedback outside File Detail, when no hunk exists, and when the
  configured clipboard handoff fails.

## Capabilities

### New Capabilities

- `file-detail-copy-hunk`: users can copy the active File Detail hunk as a
  compact review snippet.

### Modified Capabilities

无。

## Impact

- Updates `src/cr/ui/file_detail_navigation.py` to return active hunk content.
- Updates browser command parsing, command catalog, executor routing, README,
  context, and P0 docs.
- Adds focused hunk extraction, parser, catalog, and executor tests.
