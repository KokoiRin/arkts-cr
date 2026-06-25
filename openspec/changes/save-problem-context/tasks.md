## 1. Tests

- [x] 1.1 Add handoff helper tests for default and requested problem-context save paths.
- [x] 1.2 Add parser/catalog/action-bar tests for `save problem context`.
- [x] 1.3 Add BrowserCommandExecutor tests for saving Task Problems and Source File Page contexts.
- [x] 1.4 Add BrowserCommandExecutor tests for no-context and write-failure behavior.

## 2. Implementation

- [x] 2.1 Add problem-context save helper and default path in `cr.ui.handoff`.
- [x] 2.2 Add parser/catalog/action execution for `save problem context [PATH]`.
- [x] 2.3 Refactor Problem Context Markdown generation so copy and save share one path.
- [x] 2.4 Preserve current page, selection, Review Scope, and task state while saving.

## 3. Docs And Validation

- [x] 3.1 Update README, design, navigation, and P0 docs.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, compile, and diff check.
- [x] 3.3 Run Warden scope review.
