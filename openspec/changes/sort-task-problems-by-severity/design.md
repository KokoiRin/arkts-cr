## Context

`cr.ui.task_problems` owns severity facts and pure filtering. `BrowserState` owns page-local Task Problems view state such as selection, scroll, and severity filter. Severity sorting should follow the same split: pure ordering logic in `cr.ui.task_problems`, active sort mode in page-local browser state.

## Decisions

1. Default to output order.
   - Reason: existing behavior remains stable and build-log order is often meaningful.
2. Add explicit `problems sort severity`.
   - Reason: sorting is useful but should be a deliberate mode switch.
3. Add explicit `problems sort output`.
   - Reason: users need a visible way back to the original order.
4. Sort after filtering.
   - Reason: filtering defines the visible Problems list; sorting only orders what is currently visible.

## Severity Order

1. `error`
2. `warning`
3. `info`
4. `note`
5. unknown severity

Problems within each severity bucket keep task-output order.

## Boundaries

- Do not add persistence.
- Do not change extraction, severity parsing, filtering, source preview, or copy formats.
- Do not change default `problems` behavior.
