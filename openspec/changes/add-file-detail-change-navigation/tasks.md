## 1. Design

- [x] 1.1 Add OpenSpec proposal, design, tasks, and spec scenarios.
- [x] 1.2 Confirm `next change` / `prev change` do not conflict with file, hunk, or match navigation.

## 2. Implementation

- [x] 2.1 Add changed-row detection and next/previous target calculation to `file_detail_navigation`.
- [x] 2.2 Add command parsing and command catalog entries for `next change` and `prev change`.
- [x] 2.3 Execute changed-line navigation in File Detail while preserving scope, selected file, notes, progress, task state, and page.

## 3. Documentation

- [x] 3.1 Update README command usage.
- [x] 3.2 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`, and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run focused changed-line parser/navigation/executor tests.
- [x] 4.2 Run OpenSpec strict validation, compile checks, diff checks, and the full Python test suite.
- [x] 4.3 Run Warden review.
