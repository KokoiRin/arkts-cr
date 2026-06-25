## Why

Source File Page can open, search, and copy a `path:line` anchor, but AI/review handoff often needs the surrounding source, not just a location. Users should be able to copy a compact source snippet directly from the TUI after jumping from Problems or searching inside a source preview.

## What Changes

- Add `copy source` for Source File Page.
- Copy a small Markdown source context centered on the current Source File Page target line.
- Include line numbers and a target-line marker in the copied snippet.
- Advertise the action in Source File Page's contextual action bar and command catalog.

## Scope

- `source-file-snippet-copy`: source-preview handoff for current target-line context.
- `browser-command-dispatch`: route `copy source` to Source File Page clipboard behavior.

## Non-Goals

- No multi-line interactive selection.
- No syntax highlighting.
- No source editing.
- No file persistence.
- No cross-file snippets.
