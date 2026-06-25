## 1. Design

- [x] 1.1 Add OpenSpec proposal, design, tasks, and spec scenarios.
- [x] 1.2 Confirm command names do not conflict with file navigation or filters.

## 2. Implementation

- [x] 2.1 Add repeat search helper to `file_detail_navigation`.
- [x] 2.2 Add session-local last find query to `BrowserState`.
- [x] 2.3 Add `next match` / `prev match` command parsing and catalog entries.
- [x] 2.4 Execute repeat match commands in File Detail while preserving scope,
  selected file, notes, progress, and task state.

## 3. Documentation

- [x] 3.1 Update README command usage.
- [x] 3.2 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`,
  and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run focused parser/navigation/executor tests.
- [x] 4.2 Run OpenSpec strict validation, compile checks, diff checks, and the
  full Python test suite.
- [x] 4.3 Run Warden review.
