## Design

Review notes belong to `ReviewWorkspace` because they are part of the user's active review workspace, like filter state, selection, seen paths, and remaining-only mode. They do not belong to the Task Panel, command parser, file actions, or Git review facts.

The command surface is intentionally narrow:

- `note TEXT`: set or replace the selected file's note with `TEXT`.
- `note`: clear the selected file's note.

This keeps notes lightweight and easy to use from both line mode and raw-key command prompt. It also avoids adding a new page, modal editor, or multi-note database before real usage proves the need.

## Rendering

Changed Files should show a compact note marker on file rows with notes so users can see which files carry context while scanning the tree. File Detail should show the full note near the header before risks, purpose, symbols, and hunks.

## Persistence

Notes are saved in `.git/cr/browse-state.json` under a path-keyed object:

```json
{
  "review_notes": {
    "src/Sample.ts": "check lifecycle edge case"
  }
}
```

Only non-empty string notes are restored. Unknown paths can remain in the persisted object, but rendering only shows notes for current changed files. Explicit path arguments still skip workspace persistence, matching existing browse-state behavior.

## Non-Goals

- Do not add multiple notes per file.
- Do not add timestamps, author metadata, severity, or status fields.
- Do not add global scope-level notes.
- Do not add a full-screen note editor.
- Do not include notes in non-interactive `cr review --prompt` yet.
