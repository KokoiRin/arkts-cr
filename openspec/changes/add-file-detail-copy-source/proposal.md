# Add File Detail Copy Source

## Why

`view source` lets users jump from File Detail to Source File, but the most
common handoff action is often just copying the source context around the
current diff row. Requiring a page transition before `copy source` adds friction
to the File Detail -> Source -> Handoff flow.

This P0 lets File Detail copy source context directly from the current rendered
new-file line.

## What Changes

- Make the existing `copy source` command work on File Detail.
- Reuse the current diff-row new-file line mapping already used by `open line`,
  `copy line`, and `view source`.
- Copy the same Source File context Markdown shape, including best-effort symbol
  metadata when available.
- Document the command in File Detail help/action bar, README, and P0 notes.

## Non-Goals

- No deleted-only old-source preview.
- No automatic symbol-range selection.
- No source editing.
- No language-service dependency.
- No File Detail layout change.
