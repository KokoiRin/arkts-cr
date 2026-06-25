## Why

Source File Page can open a failing location and copy nearby context, but a
fixed radius is still clumsy when the useful code block is a precise method,
branch, or small multi-line expression. Users need a lightweight way to select
an exact source range without leaving the TUI or introducing an editor mode.

## What Changes

- Add `source select START END` to select a line range in the current Source
  File Page.
- Add `source clear selection` to clear the selected range.
- Render the active selection in Source File Page.
- Make `copy source` copy the selected range when one is active, while keeping
  the existing context-radius copy behavior when no selection exists.

## Non-Goals

- No source editing.
- No syntax-aware selection.
- No cross-file or multi-range selection.
- No mouse/shift selection model.
- No persistence across sessions.
