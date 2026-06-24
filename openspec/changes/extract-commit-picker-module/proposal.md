## Why

Commit Picker has become a first-layer Review Scope selector with its own
filtering, matching, change-summary search text, and filtered selection rules.
Those rules currently live in page rendering helpers and are consumed by
browser action execution, which makes the boundary blurry as the workbench
grows.

This change extracts Commit Picker rules into a dedicated `cr.ui.commit_picker`
module while preserving all user-visible behavior.

## What Changes

- Add a Commit Picker rules module for filtering, searchable text, and filtered
  selection.
- Make Browser State and Commit Picker action execution consume that module.
- Keep row rendering and empty-state text in Page Content.
- Keep command routing, prompt handling, and scope switching in `browser.py`.
- Preserve existing Commit Picker filter, numeric selection, and rendering
  behavior.

## Capabilities

### New Capabilities

- `browser-commit-picker-module`: Commit Picker filtering and filtered selection
  are owned by a dedicated UI module instead of being hidden inside page
  rendering.

### Modified Capabilities

无用户可见能力变化。

## Impact

- Adds `src/cr/ui/commit_picker.py`.
- Updates `src/cr/ui/browser.py` and `src/cr/ui/page_content.py`.
- Adds focused module tests and keeps existing Commit Picker integration tests.
- Updates architecture/product docs.
