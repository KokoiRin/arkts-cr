## Why

Commit Picker is a first-layer Review Scope selector, but filtering still follows
the old Changed Files path. Pressing `/` or typing `/query` while browsing
recent commits should narrow commits instead of switching back to files.

## What Changes

- Add a Commit Picker-local filter over loaded recent commits.
- Match filter text against commit hash, authored date, subject, and displayed
  change summary.
- Make `/`, `/QUERY`, and `filter QUERY` filter commits while Commit Picker is
  active.
- Make `c` / `clear` clear the Commit Picker filter without touching file
  filters.
- Keep Commit Picker filtering as temporary UI state; do not persist it in the
  Review Workspace.

## Capabilities

### New Capabilities
- `browser-commit-picker-filter`: filters Recent commits inside Commit Picker.

### Modified Capabilities
- None.

## Impact

- Touches `cr.ui.browser` for Commit Picker filter state and command routing.
- Touches `cr.ui.page_content` for Commit Picker filter context and empty state.
- Adds focused command, rendering, and line-mode tests.
- Updates product and architecture docs for Commit Picker filtering.
