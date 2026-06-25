## 1. Design

- [x] 1.1 Add OpenSpec proposal, design, tasks, and spec scenarios.
- [x] 1.2 Confirm `note change TEXT` reuses existing per-file review notes and does not introduce a second comments model.

## 2. Implementation

- [x] 2.1 Add command parsing and command catalog entries for `note change TEXT`.
- [x] 2.2 Add selected-file workflow that appends a current changed-row note and refreshes workspace/cache state.
- [x] 2.3 Execute `note change TEXT` in File Detail while preserving scope, selected file, progress, task state, page, and scroll.

## 3. Documentation

- [x] 3.1 Update README command usage.
- [x] 3.2 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`, and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run focused parser/action/executor tests.
- [x] 4.2 Run OpenSpec strict validation, compile checks, diff checks, and the full Python test suite.
- [x] 4.3 Run Warden review.
