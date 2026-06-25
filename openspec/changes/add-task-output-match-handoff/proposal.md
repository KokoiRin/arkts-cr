# Add Task Output Match Handoff

## Why

Task Output already supports find navigation and full/tail output handoff, but long build logs often have the useful failure wording in the middle. Users need a compact package around the current match without copying the whole log or manually selecting terminal text.

## What Changes

- Add `copy task match` to copy a Markdown excerpt around the current Task Output find focus.
- Add `save task match [PATH]` with default `.cr/handoff/task-output-match.md`.
- Include the query, focused line number, nearby output lines, and a `>` marker on the focused line.

## Non-Goals

- No new log parser.
- No task history browsing.
- No multi-match export.
- No configurable excerpt size in this slice.
- No source editing or quick fixes.
