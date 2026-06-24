## Design

`copy notes` is a review-note workflow command, not a new export subsystem. It should reuse the exact summary produced by `notes`:

```text
Review notes:
1. src/First.ts: check lifecycle edge case
2. src/Second.ts: ask owner about state reset
```

This keeps the user-facing mental model simple:

- `notes`: show the summary.
- `copy notes`: copy that same summary.
- `notes copy`: alias for the same action.

## Command Behavior

The command should:

- keep the current page, selection, review scope, and task state unchanged
- use `cr.ui.file_actions.copy_text` so `--copy-cmd` and `CR_COPY_CMD` continue to work
- report `Copied N review notes` on success
- surface copy failures using the existing file action failure message
- report `No review notes to copy.` when no notes exist, without launching a clipboard command

## Scope

This change deliberately does not add:

- file export
- note search
- prompt templates
- markdown front matter
- multiple notes per file

Those can be considered after simple copy proves useful.
