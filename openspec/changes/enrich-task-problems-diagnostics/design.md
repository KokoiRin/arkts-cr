## Context

`cr.ui.task_problems` is already the pure model boundary for current task output problems. It receives repo root plus captured output lines, extracts repo-local anchors, and formats handoff text. Page rendering lives in `cr.ui.page_content`; browser execution owns selection and clipboard/editor side effects.

## Decisions

1. Add optional facts to `TaskProblem`.
   - Reason: the existing list remains valid for unknown log formats while richer rows can display IDE-like metadata.
2. Keep parsing generic and local.
   - Reason: this P0 should improve common logs without introducing a plugin-like parser architecture before real formats demand it.
3. Preserve raw summary.
   - Reason: raw log lines are still the most trustworthy fallback. Parsed `message` is additive.
4. Render a compact label.
   - Reason: the Problems page should be scannable on a vertical terminal without adding columns or a new layout mode.

## Behavior

- `src/Foo.ets:12:3 error TS2322: bad call` becomes:
  - location: `src/Foo.ets:12:3`
  - severity: `error`
  - code: `TS2322`
  - message: `bad call`
- `src/Foo.ets:20 warning [W001]: check this` becomes severity `warning`, code `W001`, message `check this`.
- Unknown lines still produce a problem if a repo-local anchor exists, with diagnostic facts left empty.
- Handoff text includes severity/code/message when available, and falls back to the raw summary.

## Boundaries

- Do not add state to `BrowserState`.
- Do not change navigation, task lifecycle, or Source File Page behavior.
- Do not sort/filter by severity yet; output order remains task-output order.
