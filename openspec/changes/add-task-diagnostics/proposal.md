## Why

Project task presets make build/test/lint easier to run, but users still need a quick way to see which source won: CLI argument, environment variable, `.cr/tasks.json`, DouyinHarmony default, or missing. Without a diagnostic command, malformed presets are intentionally ignored and therefore hard to notice.

## What Changes

- Add a `tasks` browser command that reports build/test/lint command sources.
- Keep source resolution inside `cr.ui.tasks`.
- Report malformed `.cr/tasks.json` as diagnostic text without blocking browser startup.
- Do not start, stop, or rerun tasks from this command.

## Capabilities

### New Capabilities

- `browser-task-diagnostics`: defines task command source diagnostics for the interactive browser.

### Modified Capabilities

无。

## Impact

- Touches `src/cr/ui/tasks.py` for source diagnostics.
- Touches `src/cr/ui/commands.py` and `src/cr/ui/browser.py` to expose `tasks`.
- Adds focused tests and docs.
