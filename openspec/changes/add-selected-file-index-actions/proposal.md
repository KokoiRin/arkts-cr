## Why

`cr browse` is becoming a terminal workbench, but a common IDE workflow is still
missing: after reviewing a file, users often want to stage or unstage exactly
that file without leaving the current Changed Files / File Detail context.

The existing selected-file action model is a good fit. `stage` and `unstage`
should behave like other selected-file operations: act on the current changed
file, report a concise status message, and keep the screen hierarchy stable.

## What Changes

- Add selected-file index actions:
  - `stage`: run Git staging for the selected changed file.
  - `unstage`: remove the selected changed file from the index.
- Expose both commands through browser command parsing and the command palette.
- Refresh the active Review Scope after a successful index action so Changed
  Files reflects the new Git state.
- Keep historical/base/range Review Scopes read-only for these commands.

## Capabilities

### New Capabilities

- `browser-selected-file-index-actions`: defines selected-file `stage` and
  `unstage` commands in the interactive browser.

### Modified Capabilities

无。

## Impact

- Touches `src/cr/vcs/git.py` for Git index operations.
- Touches `src/cr/ui/commands.py` and `src/cr/ui/command_catalog.py` for command
  surface.
- Touches `src/cr/ui/selected_file_actions.py` and `src/cr/ui/browser.py` for
  selected-file workflow and post-action refresh.
- Adds focused tests and updates product/architecture docs.
