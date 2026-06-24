## Design

File action diagnostics should reuse the existing ownership split:

- `cr.ui.file_actions` owns copy/reveal template resolution, environment lookup, platform fallback, and subprocess execution.
- `cr.ui.browser` owns selected-file context and open/editor handoff.
- `cr.ui.commands` only maps command text to stable actions.

The smallest durable shape is a source object that contains:

- `kind`: `open`, `copy`, or `reveal`
- `source`: `cli`, `env`, `platform`, or `missing`
- `command`: resolved command list when available

`file actions` should show three concise lines, one per action. It should not require a changed file because diagnostics describe configuration, not the current selection. For placeholders that require selected data, diagnostics can use representative placeholders such as `{selected-file}` / `{text}`.

## Failure Messages

Failures should name the source, for example:

- `Copy failed (cli copy-tool): ...`
- `Reveal failed (platform open -R /repo/src/Foo.ts): ...`
- `No editor opener found (missing). Set --open-cmd or CR_OPEN_CMD ...`

Successful selected-file actions stay short: `Copied ...`, `Revealed ...`, `Opened ...`.

## Non-Goals

- Do not add new open/copy/reveal configuration knobs.
- Do not execute diagnostics commands.
- Do not persist diagnostics.
- Do not move all open/editor behavior into `cr.ui.file_actions` in this change.
- Do not print full resolved commands on every success.
