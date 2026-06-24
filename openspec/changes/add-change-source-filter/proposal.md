## Why

`cr browse` now shows whether local files are `staged`, `unstaged`, or `mixed`,
but users still have to scan the whole Changed Files tree to focus on one
source. A source-control panel should let the user temporarily narrow the list
to staged, unstaged, or mixed files without changing Review Scope or restarting.

## What Changes

- Add a Changed Files source filter:
  - `source staged`
  - `source unstaged`
  - `source mixed`
  - `source all` / `source clear`
- Compose source filtering with the existing path filter and `remaining` view.
- Show the active source filter in Changed Files header/filter context.
- Reset the source filter on Review Scope switches, matching other local view
  state.

## Capabilities

### New Capabilities

- `browser-change-source-filter`: filters Changed Files by local source badges.

### Modified Capabilities

无。

## Impact

- Touches `cr.ui.workspace` for source-filtered visible changes and persistence
  mapping.
- Touches `cr.ui.commands`, `cr.ui.command_catalog`, and `cr.ui.browser` for
  command parsing/execution.
- Touches `cr.ui.page_content` for header/filter context.
- Adds focused workspace, command, executor, and rendering tests.
