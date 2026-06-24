## Why

Project task presets are already useful, but the expected `.cr/tasks.json`
shape only lives in README-level prose. Inside `cr browse`, a user can inspect
the current task sources with `tasks`, but cannot ask the tool what preset file
format it expects.

## What Changes

- Add a `tasks help` browser command that explains `.cr/tasks.json`.
- Keep `tasks` as the current source diagnostics command.
- Keep the preset schema intentionally narrow: `build`, `test`, and `lint`
  string commands.
- Add a concise hint from malformed preset diagnostics to `tasks help`.

## Capabilities

### New Capabilities

- `browser-task-preset-schema-help`: defines an in-browser help surface for
  project task preset configuration.

### Modified Capabilities

- `browser-task-diagnostics`: malformed preset diagnostics can point users to
  `tasks help` without changing command resolution.

## Impact

- Touches `src/cr/ui/tasks.py` for help text and preset diagnostics.
- Touches `src/cr/ui/commands.py` for command parsing.
- Touches `src/cr/ui/browser.py` for browser execution and command catalog.
- Updates README and product architecture docs.
- Adds focused tests for parser, executor, runtime help, and palette entries.
