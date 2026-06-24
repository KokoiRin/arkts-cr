## Context

Current handoff commands split into two groups:

- Small selected-file operations: `copy path`, `copy anchor`, `open`, `reveal`,
  `stage`, `unstage`, and `note`.
- Full review handoff operations: `copy prompt`, `copy prompt file`,
  `save prompt`, and `save prompt file`.

`copy prompt file` is intentionally AI-prompt shaped. It includes an overall
handoff title and request language. That is heavier than the common workflow of
copying just the current file's review diff context.

## Goals / Non-Goals

**Goals:**

- Add `copy diff` as a selected-file browser action.
- Generate a compact Markdown snippet for exactly the selected visible file.
- Include path, status/summary, anchor, seen state, review note, purpose/focus,
  risks, and diff hunks when available.
- Reuse existing `.cr` copy command configuration through File Actions.
- Keep the current page and workspace state unchanged.

**Non-Goals:**

- No `save diff` command in this change.
- No raw `git diff` patch mode.
- No multi-file diff copy; users can still use `copy prompt` for scope-level
  handoff.
- No new browser page or persisted state.

## Decisions

### Decision 1: Review owns snippet text

The snippet renderer lives in `cr.review.snippet`, not `cr.ui.browser`, because
it is review content, not terminal interaction. Browser selected-file actions
choose which file to render and how to copy it.

### Decision 2: Use structured review data

Selected-file diff copy uses `build_review_data()` for a one-file list. That
keeps hunk context, first changed line, purpose, focus, risk, seen, and review
note behavior aligned with existing review and prompt output.

### Decision 3: Keep command simple

The user command is `copy diff`. The command has no arguments, no mode switch,
and no persistence. Future save/export variants can reuse the same snippet
renderer without expanding this first slice.

## Risks / Trade-offs

- The snippet is Markdown, not an exact patch. This is deliberate: the goal is a
  readable review snippet that preserves existing review facts, not a patch that
  can be applied.
- `copy prompt file` and `copy diff` overlap slightly. The distinction is
  intent: prompt file is AI-request shaped; diff copy is lightweight selected
  file context.
