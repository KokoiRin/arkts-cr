## Design

`tasks help` is a browser command, not a task process. It should render a small
plain-text help block through the same output path used by `tasks` diagnostics.

The help text belongs in `cr.ui.tasks` because that module owns task command
resolution and preset parsing. `cr.ui.commands` only maps the command language
to a stable action, and `cr.ui.browser` only chooses how to display the returned
lines.

## Scope

Supported preset file:

```json
{
  "build": "./remote buildEntry --app douyin",
  "test": "npm test",
  "lint": "npm run lint"
}
```

Each value is a shell-like command string. The runtime still resolves commands
with the existing priority:

`CLI args > environment variables > .cr/tasks.json > DouyinHarmony default > missing`

## Non-Goals

- Do not add a full JSON Schema file.
- Do not add a preset editor.
- Do not add new task kinds.
- Do not make malformed `.cr/tasks.json` fatal.
