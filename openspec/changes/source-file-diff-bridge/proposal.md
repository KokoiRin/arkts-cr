# Change: Source File diff bridge

## Why

After a build/test/lint problem opens Source File, users often inspect the surrounding source and then need to compare it with the current diff. Today `view problem diff` works from Task Output and Task Problems, but Source File requires going back first. That breaks the fast Problems -> Source -> Diff loop.

## What Changes

- Add a Source File action for `view diff` and existing `view problem diff`.
- When the current source path exists in the active review scope, open File Detail for that file.
- Try to scroll File Detail to the current Source File line when that line is visible in the rendered diff.
- Keep existing Task Output and Task Problems `view problem diff` behavior unchanged.

## Non-Goals

- No language-service lookup.
- No synthetic diffs for unchanged files.
- No source editing, quick fixes, or cross-file dependency expansion.
- No new persisted problem-origin state.
