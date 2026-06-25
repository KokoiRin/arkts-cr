# Add Copy Source Symbol

## Why

`source select symbol` and File Detail `copy source` cover two useful handoff
shapes, but copying a whole method/function still takes multiple steps from
File Detail:

```text
view source -> source select symbol -> copy source
```

For AI handoff, the common desired payload is often the enclosing method or
function block. This P0 adds one direct command for that shape.

## What Changes

- Add `copy source symbol`.
- On Source File, copy the innermost best-effort symbol containing the current
  source line.
- On File Detail, map the current diff row to a new-file line, then copy the
  innermost best-effort symbol containing that line.
- Keep existing `copy source` behavior unchanged.
- Document the command in help, command catalog, README, and P0 notes.

## Non-Goals

- No language-server dependency.
- No full ArkTS/TypeScript parser.
- No automatic source selection state change.
- No old-source deleted-row preview.
- No source editing.
