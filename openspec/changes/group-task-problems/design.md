## Demand Card

Implement file grouping for Task Problems.

Expected behavior:

- Input: `problems group file` and `problems group none`.
- Output: Task Problems page optionally renders file headers followed by visible
  problem rows for that file.
- Composition: grouping applies after severity filtering, text query filtering,
  and sorting have produced the visible list.
- Actions: selection and all existing problem actions still use the visible
  `TaskProblem` list, not group headers.
- Lifecycle: grouping is page-local, resets to `none` for newly opened Problems,
  and is restored through page history snapshots.

Not doing:

- Group collapsing, group navigation, group copy/open, task history grouping,
  persistence, or tool-specific parser registries.

Acceptance:

- Parser/catalog/action bar expose group commands.
- Rendering shows file headers and preserves visible problem indices.
- Selection/open/copy continue to use the same filtered/sorted visible list.
- Docs record trigger, composition, lifecycle, and non-goals.

## Design

Task Problems already has page-local `problem_filter`, `problem_query`, and
`problem_sort`. Grouping should follow the same state pattern:

- Add `BrowserState.problem_group` with values `none` and `file`.
- Snapshot/restore `problem_group` in `BrowserNavigation`.
- Add command parsing for `problems group file` and `problems group none`.
- Render grouping in `cr.ui.page_content.task_problems_screen_lines`.

The grouping is render-only. `_current_task_problems` remains the single source
for action behavior: it applies severity filter, text query, and sort. Page
content may insert file header lines around rows, but it must keep row labels
using the problem's visible list index so the user sees stable row numbers.

## Boundaries

This is a readability improvement for the current Problems page. It should not
create a diagnostics database, change task output extraction, or introduce a
tree-selection model before real usage proves that need.
