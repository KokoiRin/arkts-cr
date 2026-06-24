## 1. Commit Picker Module

- [x] 1.1 Add focused tests for Commit Picker filtering and filtered selection.
- [x] 1.2 Add `cr.ui.commit_picker` with pure filtering/search/selection helpers.

## 2. Integration

- [x] 2.1 Make `BrowserState.visible_commits` use the Commit Picker module.
- [x] 2.2 Make Commit Picker selection use the module-owned filtered list.
- [x] 2.3 Make Page Content render Commit Picker rows from the module-owned filter.

## 3. Documentation

- [x] 3.1 Update `CONTEXT.md`.
- [x] 3.2 Update `docs/design.md`, `docs/workbench-navigation.md`, and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run OpenSpec strict validation.
- [x] 4.2 Run focused Commit Picker tests.
- [x] 4.3 Run compile checks, diff checks, and the full Python test suite.
- [x] 4.4 Run Warden review.
