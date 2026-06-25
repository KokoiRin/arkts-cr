## 1. Design

- [x] 1.1 Add OpenSpec proposal, design, tasks, and spec scenarios.
- [x] 1.2 Confirm `open line` / `copy line` do not change existing file-level or hunk-level actions.

## 2. Implementation

- [x] 2.1 Add rendered current-line new-file line parsing to `file_detail_navigation`.
- [x] 2.2 Add selected-file `open line` and `copy line` workflows.
- [x] 2.3 Add command parsing and command catalog entries for `open line` and `copy line`.
- [x] 2.4 Execute line actions in File Detail while preserving scope, selected file, notes, progress, task state, page, and scroll.

## 3. Documentation

- [x] 3.1 Update README command usage.
- [x] 3.2 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`, and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run focused line-action parser/navigation/action/executor tests.
- [x] 4.2 Run OpenSpec strict validation, compile checks, diff checks, and the full Python test suite.
- [x] 4.3 Run Warden review.
