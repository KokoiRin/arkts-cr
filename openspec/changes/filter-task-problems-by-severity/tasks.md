## 1. Tests

- [x] 1.1 Add pure filtering tests for severity and output-order preservation.
- [x] 1.2 Add command parser/catalog tests for severity filter commands.
- [x] 1.3 Add navigation/page-content tests for filter state, header, and empty state.
- [x] 1.4 Add BrowserCommandExecutor tests proving open/copy operate on filtered problems.

## 2. Implementation

- [x] 2.1 Add page-local `problem_filter` to browser/navigation state snapshots.
- [x] 2.2 Add `filter_task_problems` in `cr.ui.task_problems`.
- [x] 2.3 Add parser/catalog entries and executor handling for severity filter commands.
- [x] 2.4 Apply the filtered list to render/move/open/view/copy flows.

## 3. Docs And Validation

- [x] 3.1 Update README, design, navigation, and P0 docs.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, compile, and diff check.
- [x] 3.3 Run Warden scope review.
