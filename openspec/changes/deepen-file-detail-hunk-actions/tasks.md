## 1. Design

- [x] 1.1 Add OpenSpec proposal, design, tasks, and spec scenarios.
- [x] 1.2 Confirm module ownership against `CONTEXT.md` and current code.

## 2. Implementation

- [x] 2.1 Add selected-file hunk open/copy helpers.
- [x] 2.2 Route browser `open hunk` / `copy hunk` through the helpers while
  preserving page checks, selection, status messages, and redraw behavior.
- [x] 2.3 Keep hunk parsing/extraction in `file_detail_navigation`.

## 3. Documentation

- [x] 3.1 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`,
  and `docs/p0.md` with the deeper hunk action ownership.

## 4. Verification

- [x] 4.1 Run focused selected-file hunk action and browser executor tests.
- [x] 4.2 Run OpenSpec strict validation, compile checks, diff checks, and the
  full Python test suite.
- [x] 4.3 Run Warden review.
