## Why

`cr browse` now has clear product layers: Review Scope, Changed Files, File Detail, Command Palette, Scope Home, and Commit Picker. Back behavior is still hierarchy-aware but not historical: users cannot return to the exact page they came from, and there is no forward path after going back. A terminal workbench that aims to replace IDE habits needs predictable page history.

## What Changes

- Add a browser page stack for in-session page transitions.
- Preserve the previous page's local selection and scroll state when moving back.
- Add a `forward` command to return to the page popped by `back`.
- Keep review scope switching and Git data loading in `ReviewWorkspace`.
- Keep workspace persistence unchanged for this P0.

## Capabilities

### New Capabilities

- `browser-page-stack`: defines in-session page back/forward history for the interactive browser.

### Modified Capabilities

无。

## Impact

- Touches `src/cr/ui/navigation.py` for page history state and transition rules.
- Touches `src/cr/ui/commands.py` and `src/cr/ui/browser.py` for `forward`.
- Adds focused navigation/action tests and docs.
