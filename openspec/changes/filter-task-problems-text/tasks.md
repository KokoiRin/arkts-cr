## 1. Tests

- [x] 1.1 Add pure query-filter tests covering path, summary, severity, code, and message.
- [x] 1.2 Add parser/catalog/action-bar tests for query commands.
- [x] 1.3 Add navigation/page-content tests for query reset, restore, and header display.
- [x] 1.4 Add BrowserCommandExecutor tests proving copy/open use queried visible problems.

## 2. Implementation

- [x] 2.1 Add page-local `problem_query` to browser/navigation snapshots.
- [x] 2.2 Add `filter_task_problems_by_query` in `cr.ui.task_problems`.
- [x] 2.3 Add parser/catalog/action execution for `problems find TEXT` and `problems clear find`.
- [x] 2.4 Apply severity filter, then query filter, then sort in `_current_task_problems`.
- [x] 2.5 Render query state in Task Problems page.

## 3. Docs And Validation

- [x] 3.1 Update README, design, navigation, and P0 docs.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, compile, and diff check.
- [x] 3.3 Run Warden scope review.
