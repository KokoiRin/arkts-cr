## Design

This is a module deepening change. The external product interface stays the same:

- `open` opens the selected changed file at the first changed line when possible.
- `--open-cmd` wins over `CR_OPEN_CMD`.
- Editor fallbacks prefer GUI editor commands that support line anchors.
- Missing or failed open commands return a user-visible message.

The ownership change is:

- `cr.ui.file_actions` owns open/copy/reveal source resolution, command formatting, platform fallback, and subprocess execution.
- `cr.ui.browser` owns review context: selected changed file, current review scope flags, first changed line lookup, and message/status rendering.
- `cr.ui.commands` remains command parsing only.

## Interface

`cr.ui.file_actions` should expose the same style of deep module interface for open as it already does for copy/reveal:

- `open_path(path, line, configured=None) -> str | None`
- `open_command(path, line, configured=None) -> list[str] | None`
- `open_command_source(path, line, configured=None) -> FileActionCommandSource`

Callers do not need to know about `CR_OPEN_CMD`, `code -g`, `cursor -g`, `open`, or template placeholders. The module hides that knowledge behind the source object and success/error message.

## Template Placeholders

Open command templates continue to support:

- `{file}`: absolute file path
- `{line}`: first changed line or `1`
- `{fileline}`: `path:line`

## Testing Strategy

Tests should move open command resolution coverage to `cr.ui.file_actions`, then keep browser executor tests focused on selected-file behavior:

- browser calls file action open with the repo file and first changed line
- browser reports no-file feedback when no changed file is selected
- file action diagnostics include open/copy/reveal source lines
- file action module preserves configured/env/platform/missing open behavior

## Non-Goals

- Do not add new editor integrations.
- Do not add an editor selection UI.
- Do not change command names, aliases, or command palette behavior.
- Do not change copy/reveal behavior.
