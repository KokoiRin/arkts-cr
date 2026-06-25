## Why

`copy problem context` gives users a focused package for AI/chat, but clipboard
handoff is fragile in remote terminals and the context is sometimes worth
keeping as an artifact. Users need the same focused problem/source/diff context
saved to disk without rebuilding it manually.

## What Changes

- Add `save problem context [PATH]`.
- Default to `.cr/handoff/problem-context.md` when no path is provided.
- Save the same Markdown produced by `copy problem context`.
- Report clear empty, unreadable-source, and write-failure messages.

## Non-Goals

- No batch saving multiple problems.
- No task transcript or raw output persistence.
- No prompt template expansion.
- No cross-file dependency collection.
- No workspace-state persistence.
