## Design

Review notes summary is a command-level surface, not a new navigation page. The product already has three review layers:

- Review Scope: worktree, staged, all local changes, base ref, or ref range.
- Changed Files: the file tree/list inside the active scope.
- File Detail: one changed file's detail view.

`notes` sits beside diagnostics-style commands such as `tasks` and `file actions`: it reports useful workspace information without changing the user's current layer, selection, task process, or review scope. This keeps the interaction lightweight while the higher-level navigation model stays stable.

## Ordering

The summary should make the active review scope easy to scan:

1. Notes for paths present in `state.changes`, ordered exactly like the current review list.
2. Notes persisted in `state.review_notes` for paths that are no longer in `state.changes`, ordered by path.

This preserves the user's current mental map while still making stale or out-of-scope notes visible instead of silently hiding them.

## Rendering

Line mode prints a compact multi-line block:

```text
Review notes:
1. src/First.ts: check lifecycle edge case
2. src/Second.ts: ask owner about state reset
```

Raw-key mode uses the status/message area with a single compact string so the main screen remains stable. The command should not open a modal, enter an editor, or steal the task panel.

## Non-Goals

- Do not add note search.
- Do not export notes to a file or prompt.
- Do not add multiple notes per file.
- Do not add a dedicated notes page yet.
- Do not change workspace persistence shape.
