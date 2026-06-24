## Why

Scope Home is the first review layer, but it currently lists entry points
without showing whether each one contains work. Users should be able to glance
at Worktree, Staged, All local changes, and Recent commits before entering a
scope.

## What Changes

- Show live counts beside Scope Home entries:
  - Worktree changed-file count.
  - Staged changed-file count.
  - All local changes changed-file count.
  - Recent commits count.
- Load these counts when Scope Home is opened or refreshed.
- Keep counts as temporary UI state; do not persist them in workspace state.
- Leave Base ref and Explicit range as parameterized command hints without
  counts.

## Capabilities

### New Capabilities
- `browser-scope-home-counts`: displays live overview counts on the Review Scope
  Home page.

### Modified Capabilities
- None.

## Impact

- Touches `cr.ui.browser` for count sampling when entering Scope Home.
- Touches `cr.ui.page_content` for Scope Home row rendering.
- Adds focused tests for count rendering and refresh/loading behavior.
- Updates product and architecture docs for the Scope Home overview.
