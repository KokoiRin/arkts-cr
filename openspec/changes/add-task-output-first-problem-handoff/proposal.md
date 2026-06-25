# Add Task Output First Problem Handoff

## Why

After a build/test/lint failure, users often land on Task Output first. Today
they must run `problems`, then `view problem` or `copy problem context` from
Task Problems. That is clear but still adds a page hop for the most common
debugging move: open the first parseable failure or hand it back to AI.

This P0 tightens the Build -> Problems -> Source -> Handoff loop by allowing
Task Output to act on the first visible parsed problem directly.

## What Changes

- On Task Output, `view problem` opens the source preview for the first visible
  parsed task problem.
- On Task Output, `copy problem context` and `save problem context` use that
  same first visible parsed task problem.
- Task Problems behavior remains unchanged: it still acts on the selected
  problem.
- Task Output help, action bar, README, and P0 docs mention the direct handoff.

## Non-Goals

- No new task-output parser.
- No automatic navigation after task failure.
- No new persisted diagnostic state.
- No task history browsing.
- No source editing or quick-fix execution.
