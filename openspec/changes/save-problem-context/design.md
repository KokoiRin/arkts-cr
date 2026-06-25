## Demand Card

Implement durable Problem Context handoff.

Expected behavior:

- Input: `save problem context [PATH]` from Task Problems or Source File Page.
- Output: write focused Markdown containing problem facts when available,
  source context around the target line, and same-file diff when the file is in
  current Review Scope.
- Default path: `.cr/handoff/problem-context.md`.
- Error behavior: no active problem/source reports no context; unreadable source
  reports the source error; write errors report the destination path and leave
  browser state unchanged.

Not doing:

- Batch context saves, history, task transcript saving, templates, dependency
  discovery, or persisted source/task diagnostics.

Acceptance:

- Parser/catalog expose `save problem context`.
- Browser command saves from Task Problems and Source File Page.
- Saved Markdown matches the copy path's generated context.
- Docs record trigger, default path, and boundaries.

## Design

Existing `copy problem context` already gathers the selected Task Problem or
Source File Page target, formats source context through `cr.ui.source_file`,
adds current-scope same-file diff through `cr.review.snippet`, and assembles
Markdown through `cr.ui.problem_context`.

The save command should reuse that same generation path:

- Extract pure `_problem_context_text(...)` in `browser.py` returning text plus
  anchor, or an error message.
- Keep clipboard and file-write side effects at Browser Action Execution.
- Add `handoff.save_problem_context_text(...)` with a new default path constant.
- Add `SAVE_PROBLEM_CONTEXT` parsing and command-catalog entries.

## Boundaries

This is a handoff-file feature, not a diagnostics database. It should not write
workspace persistence, change task lifecycle, or invent a new problem model.
