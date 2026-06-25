## Context

`cr.ui.task_problems` already owns extracted diagnostic facts and pure severity filtering. `cr.ui.page_content` renders the Problems page. Counts are display facts derived from the same visible list that the page already renders, so they should not introduce browser state.

## Decisions

1. Count the visible list only.
   - Reason: `page_content` receives the same filtered list used by movement/open/copy. Showing visible counts avoids adding total-problem state or a second data source.
2. Put count formatting in `cr.ui.task_problems`.
   - Reason: severity vocabulary and unknown-severity handling are domain rules, not rendering layout.
3. Keep unknown anchors visible but separate.
   - Reason: logs without recognized severity should remain understandable as `unknown` rather than being silently omitted from counts.

## Behavior

- A visible list with two errors, one warning, and one unknown row renders a header containing `2 errors, 1 warning, 1 unknown`.
- A filtered error list renders counts for visible errors only.
- Empty filtered state remains unchanged and does not show a misleading zero-count badge.

## Boundaries

- Do not add `BrowserState` fields.
- Do not change filtering, selection, open, source preview, copy, or task lifecycle behavior.
