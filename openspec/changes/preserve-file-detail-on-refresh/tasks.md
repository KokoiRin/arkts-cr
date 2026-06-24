## 1. Design

- [x] 1.1 Add OpenSpec proposal, design, tasks, and scenarios.
- [x] 1.2 Confirm current refresh and stage/unstage refresh behavior.

## 2. Implementation

- [x] 2.1 Add ReviewWorkspace reload helper that preserves selection by path.
- [x] 2.2 Preserve File Detail on ordinary refresh when the selected path
  survives the refreshed visible changes.
- [x] 2.3 Fall back to Changed Files when the selected path is gone.
- [x] 2.4 Keep mutating index-action refresh behavior unchanged.

## 3. Documentation

- [x] 3.1 Update README refresh behavior.
- [x] 3.2 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`,
  and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run focused refresh and workspace tests.
- [x] 4.2 Run OpenSpec strict validation, compile checks, diff checks, and the
  full Python test suite.
- [x] 4.3 Run Warden review.
