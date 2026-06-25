## Why
Source File Page already supports `source select START END`, but that still
requires typing exact line numbers while inspecting a problem. For IDE-like
daily use, users should be able to mark the current source line, move or find
another line, and select the range between them without leaving the TUI flow.

## What Changes
- Add a page-local source mark for Source File Page.
- Add `source mark` to remember the current source target line.
- Add `source select to` to select the range from the mark to the current target
  line.
- Add `source clear mark` to clear the mark without clearing an existing
  selection.
- Show the active mark in Source File Page rendering, help, and command catalog.

## Impact
- Affects Source File Page selection ergonomics only.
- Existing `source select START END`, `source clear selection`, and `copy source`
  behavior remains unchanged.
