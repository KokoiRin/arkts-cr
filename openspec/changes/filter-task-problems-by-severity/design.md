## Context

`cr.ui.task_problems` owns extraction and formatting of current task output problems. `BrowserState` already owns Task Problems page-local selection and scroll. Filtering should be another page-local view state, not a Review Workspace or task runtime concern.

## Decisions

1. Store `problem_filter` on `BrowserState`.
   - Reason: selection, scroll, and filter describe the visible Problems page. Back/forward snapshots should restore them together.
2. Keep filtering pure in `cr.ui.task_problems`.
   - Reason: browser flows should not duplicate severity matching across render/open/copy/move.
3. Do not sort.
   - Reason: task output order is still the most trustworthy ordering. Filtering narrows the list without reordering it.
4. Opening `problems` clears the filter; severity commands open Problems with the requested filter.
   - Reason: `problems` remains the all-problems entry point, while `problems errors` and aliases are explicit focus commands.

## Commands

- `problems errors` / `errors`: show only error task problems.
- `problems warnings` / `warnings`: show only warning task problems.
- `problems info`: show only info task problems.
- `problems note`: show only note task problems.
- `problems all` / `all problems`: clear the severity filter.

## Behavior

- Selection and scroll reset when the filter changes.
- Enter/open, `view problem`, `copy problem`, and `copy problems` operate on the filtered visible list.
- If a filter has no matches, the page shows a filter-specific empty state instead of the generic no-output empty state.
- Back/forward restores the filter through `BrowserPageSnapshot`.
