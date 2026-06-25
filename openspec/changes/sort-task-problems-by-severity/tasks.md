## 1. Tests

- [x] 1.1 Add pure sorting tests for severity order and output-order fallback.
- [x] 1.2 Add command parser/catalog tests for sort commands.
- [x] 1.3 Add navigation/page-content tests for sort state and header display.
- [x] 1.4 Add BrowserCommandExecutor tests proving open/copy operate on sorted visible problems.

## 2. Implementation

- [x] 2.1 Add page-local `problem_sort` to browser/navigation state snapshots.
- [x] 2.2 Add `sort_task_problems` in `cr.ui.task_problems`.
- [x] 2.3 Add parser/catalog entries and executor handling for sort commands.
- [x] 2.4 Apply sort after filtering in the current Problems list.

## 3. Docs And Validation

- [x] 3.1 Update README, design, navigation, and P0 docs.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, compile, and diff check.
- [x] 3.3 Run Warden scope review.
