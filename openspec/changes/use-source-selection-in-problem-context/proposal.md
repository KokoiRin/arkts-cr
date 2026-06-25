## Why

Source File Page can select a source range or the current symbol, and `copy
source` respects that selection. `copy problem context` still ignores it and
falls back to a small line-context window. After users inspect a failing
function and select the relevant block, the handoff package should preserve
that chosen range instead of requiring a separate source copy.

## What Changes

- Make Source File `copy problem context` and `save problem context` use the
  active source selection when one exists.
- Preserve existing line-context behavior when no selection exists.
- Keep Task Output and Task Problems problem context unchanged.

## Non-Goals

- No automatic symbol selection side effect.
- No multi-file dependency collection.
- No language-server or parser dependency.
- No source editing or quick fixes.
- No new persisted selection state.
