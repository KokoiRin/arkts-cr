## Why

Source File Page lets users inspect code around task problems without leaving the TUI. After finding or scrolling to the relevant source line, users need the same lightweight handoff primitive they already use in File Detail: copy a stable `path:line` anchor for the current line.

## What Changes

- `copy line` works on Source File Page.
- The copied text is the current Source File Page target anchor: `path:line`.
- Source File Page action bar advertises `copy line`.
- Existing File Detail `copy line` behavior remains unchanged.

## Scope

- `source-file-copy-line`: Source File Page line-anchor clipboard behavior.
- `browser-command-dispatch`: existing `copy line` command dispatches by active page.

## Non-Goals

- No source text snippet format.
- No multi-line selection.
- No editing, diagnostics persistence, or cross-file source search.
- No changes to File Detail line resolution.
