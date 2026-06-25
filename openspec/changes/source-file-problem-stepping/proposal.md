# Change: Source File problem stepping

## Why

After `view problem` opens Source File, users often want to scan several build/test/lint problems in source form. Today `next problem` and `prev problem` move the selected problem index, but Source File stays on the old path and line. That forces users back to Task Problems or Task Output between every source preview.

## What Changes

- On Source File, `next problem` opens the next parsed task problem in Source File.
- On Source File, `prev problem` opens the previous parsed task problem in Source File.
- Existing Task Output and Task Problems problem-selection behavior remains unchanged.

## Non-Goals

- No persisted diagnostics.
- No new problem-origin state.
- No multi-select problem review.
- No quick fixes, source editing, or language-service integration.
