## 1. Tests

- [x] 1.1 Add command parser/catalog tests for `source context N`.
- [x] 1.2 Add navigation/page-content tests for radius reset, snapshot restore, and header display.
- [x] 1.3 Add BrowserCommandExecutor tests proving `copy source` uses the active radius.
- [x] 1.4 Add invalid/clamped radius tests.

## 2. Implementation

- [x] 2.1 Add page-local `source_context_lines` to browser/navigation state snapshots.
- [x] 2.2 Add parser/catalog entries and executor handling for `source context N`.
- [x] 2.3 Pass the active radius into `source_context_markdown`.
- [x] 2.4 Render the active radius on Source File Page.

## 3. Docs And Validation

- [x] 3.1 Update README, design, navigation, and P0 docs.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, compile, and diff check.
- [x] 3.3 Run Warden scope review.
