## Design

`notes QUERY` is a read-only filter over the existing review notes summary. It should not introduce a new page, persistent filter state, or note database. The command is intentionally stateless:

- `notes`: show all notes.
- `notes QUERY`: show matching notes for this command only.
- `copy notes` / `notes copy`: continue copying the full notes summary.

## Matching

The query is trimmed and matched case-insensitively against:

- the full repo-relative path stored in `review_notes`
- the note text

Display continues to use shortened paths for readability.

## Rendering

All notes:

```text
Review notes:
1. src/First.ts: check lifecycle
```

Filtered notes:

```text
Review notes matching "life":
1. src/First.ts: check lifecycle
```

No filtered matches:

```text
Review notes matching "owner": none
```

No notes at all remains:

```text
Review notes: none
```

## Non-Goals

- Do not persist a notes filter.
- Do not change Changed Files filtering.
- Do not add fuzzy matching or regex.
- Do not change `copy notes` to copy filtered notes.
- Do not add export-to-file or prompt templates.
