## Why

Task Output can jump to or copy context for a parsed problem, but it currently
always targets the first visible problem. When a build log has several errors,
users must open Task Problems just to move the handoff target. That slows the
common build-failure flow: read log, select the relevant problem, view source,
copy context back to AI.

## What Changes

- Add `next problem` and `prev problem` commands for parsed task problems.
- Let Task Output use the current problem selection for `view problem`,
  `copy problem context`, and `save problem context`.
- Show the selected problem index/location in the Task Output header.
- Keep Task Problems selection behavior unchanged.

## Non-Goals

- No new task-output parser.
- No multi-select problem operations.
- No task history browsing.
- No persisted diagnostic selection.
- No source editing, quick fixes, or language-server integration.
