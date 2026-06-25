## Why

`copy problem context` and `save problem context` already package the selected
Problem with source and diff context, but build failures often need the nearby
task output line to preserve compiler wording, stack context, or command noise.
Users should not have to switch back to Task Output and manually copy the same
few lines before handing the issue to AI.

## What Changes

- Include a small Task Output excerpt in Problem Context Markdown when the
  context is generated from Task Output or Task Problems.
- Center the excerpt on the selected problem's captured output line.
- Keep Source File Page problem context unchanged because it does not have an
  active task-output diagnostic.

## Non-Goals

- No new task-output parser.
- No task history browsing.
- No full task transcript in problem context.
- No configurable excerpt size.
- No source editing, quick fixes, or language-server integration.
