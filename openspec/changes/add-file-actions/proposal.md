## Why

`cr browse` already lets users open the selected changed file at its first changed line, but everyday review work also needs quick file operations that do not leave the terminal: copying the selected path, copying a stable review anchor, and revealing the file in the system file browser. These should reuse the existing command parser, command palette, and browser action executor instead of becoming ad-hoc key handlers.

## What Changes

- Add file actions for the selected changed file:
  - `copy path`: copy the repo-relative path.
  - `copy anchor`: copy `path:line` using the first changed line when available.
  - `reveal`: reveal the file in the OS file browser.
- Add command parser actions and command palette entries for those actions.
- Keep `open` as the editor handoff to the first changed line.
- Show action feedback in the existing browser status/message area.

## Capabilities

### New Capabilities

- `browser-file-actions`: defines selected-file copy and reveal actions in the interactive browser.

### Modified Capabilities

无。

## Impact

- Touches `src/cr/ui/commands.py` for command parsing.
- Touches `src/cr/ui/browser.py` for action execution and command catalog entries.
- May add a small UI helper module for clipboard/reveal side effects.
- Adds focused command/action tests and docs.
