## Why

Source File Page can show the current symbol and copy/select symbol ranges, but
reading a long ArkTS file still requires scrolling line by line or text search.
After jumping from a build problem into source, users often need to inspect the
previous or next method/function before deciding what context to hand back to
AI.

## What Changes

- Add `next symbol` and `prev symbol` commands on Source File Page.
- Move the current source line to the next/previous recognized symbol start.
- Reuse the existing lightweight outline, current-symbol header, and source
  copy/select commands.

## Non-Goals

- No outline tree panel.
- No language-server dependency.
- No cross-file symbol navigation.
- No source editing, quick fixes, or refactors.
- No persisted symbol selection state.
