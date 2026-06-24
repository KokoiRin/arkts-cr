## Why

`copy path`, `copy anchor`, and `reveal` make selected-file operations usable inside `cr browse`, but copy/reveal currently rely on built-in platform fallbacks. A terminal workbench should let users adapt those actions to their terminal, desktop, or editor setup without editing code.

## What Changes

- Add `--copy-cmd` / `CR_COPY_CMD` for `copy path` and `copy anchor`.
- Add `--reveal-cmd` / `CR_REVEAL_CMD` for `reveal`.
- Keep built-in platform fallbacks when no command is configured.
- Keep `open` behavior and `--open-cmd` unchanged.

## Capabilities

### New Capabilities

- `browser-file-action-configuration`: defines user-configurable copy and reveal file actions for the interactive browser.

### Modified Capabilities

无。

## Impact

- Touches `src/cr/cli.py` for new browse options.
- Touches `src/cr/ui/file_actions.py` for configured command execution.
- Touches `src/cr/ui/browser.py` to pass configured commands to file action helpers.
- Adds focused tests and docs.
