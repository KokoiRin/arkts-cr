## 1. Design

- [x] 1.1 Add OpenSpec proposal, design, tasks, and spec scenarios.
- [x] 1.2 Confirm `done next` composes existing seen progress and file navigation without changing `m` or `n`.

## 2. Implementation

- [x] 2.1 Add command parsing and command catalog entry for `done next` / `seen next`.
- [x] 2.2 Add executor helper that marks current visible file seen and moves to the correct next visible file across normal and remaining-only views.
- [x] 2.3 Preserve Changed Files vs File Detail layer behavior while updating selection, scroll, status, and workspace state.

## 3. Documentation

- [x] 3.1 Update README command usage.
- [x] 3.2 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`, and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run focused parser/executor tests.
- [x] 4.2 Run OpenSpec strict validation, compile checks, diff checks, and the full Python test suite.
- [x] 4.3 Run Warden review.
