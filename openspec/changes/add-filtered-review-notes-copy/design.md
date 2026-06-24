## Design

`copy notes QUERY` composes two existing concepts:

- `notes QUERY`: produce a filtered review notes summary.
- `copy notes`: copy a review notes summary through the configured clipboard action.

The new command should copy exactly the same text that `notes QUERY` would display for matches:

```text
Review notes matching "life":
1. src/First.ts: check lifecycle
```

## Command Behavior

- `copy notes`: copy all notes.
- `copy notes QUERY`: copy matching notes only.
- `notes copy`: keep the existing alias for copying all notes.

The command should not persist a query, alter file filters, change page/selection/scope, or affect running tasks.

## Empty States

- If there are no notes at all: `No review notes to copy.`
- If notes exist but none match the query: `No matching review notes to copy.`

Neither empty state should call the clipboard command.

## Non-Goals

- Do not add `notes copy QUERY`.
- Do not add export-to-file.
- Do not add prompt templates.
- Do not add fuzzy matching or regex.
