## 1. Tests

- [x] 1.1 Add pure source-file tests for selected-row facts and selected-range Markdown.
- [x] 1.2 Add parser/catalog/action-bar tests for selection commands.
- [x] 1.3 Add navigation/page-content tests for selection reset, restore, and rendering.
- [x] 1.4 Add BrowserCommandExecutor tests for setting, clearing, invalid selection, and `copy source`.

## 2. Implementation

- [x] 2.1 Add page-local source selection state and snapshots.
- [x] 2.2 Add source range normalization, selected-row facts, and selected Markdown in `cr.ui.source_file`.
- [x] 2.3 Add parser/catalog/action execution for `source select START END` and `source clear selection`.
- [x] 2.4 Render selection state in Source File Page.
- [x] 2.5 Route `copy source` to selected range when active.

## 3. Docs And Validation

- [x] 3.1 Update README, design, navigation, and P0 docs.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, compile, and diff check.
- [x] 3.3 Run Warden scope review.
