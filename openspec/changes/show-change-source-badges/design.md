## Context

The product hierarchy stays:

```text
Review Scope
  -> Changed Files
    -> File Detail
```

Change source badges belong to Changed Files. They answer "where is this local
change currently sitting relative to the Git index?" They are not a new page,
not a filter, and not a replacement for staged/worktree/all Review Scopes.

## Requirement Card

## Requirement

Show local change source badges for changed files in `cr browse`.

## Expected Behavior

- Local unstaged/worktree changes carry source `unstaged`.
- Local staged/index changes carry source `staged`.
- `--all` local changes carry:
  - `staged` when the path only has staged changes.
  - `unstaged` when the path only has unstaged changes.
  - `mixed` when the path has both staged and unstaged changes.
- Browser Changed Files rows show the source badge next to file metadata.
- Base/range/commit scopes do not show source badges because they are read-only
  comparisons, not current mutable index/worktree locations.

## Not Doing

- No new filtering by source.
- No new sorting by source.
- No JSON schema change for `cr review --json`.
- No changes to hunk rendering or first-changed-line calculation.
- No additional Git mutation commands.

## Acceptance Criteria

- `git.changed_files(..., staged=True)` returns changes with `source="staged"`.
- `git.changed_files(..., staged=False)` returns tracked worktree changes with
  `source="unstaged"` and leaves untracked status behavior intact.
- `git.changed_files(..., all_changes=True)` marks per-path source as staged,
  unstaged, or mixed.
- Browser Changed Files rows render source badges without breaking progress,
  notes, status, or tree layout.
- Existing review/diff output remains compatible.

## Module Shape

Dependency category: local Git subprocess boundary.

The useful seam is:

```text
cr.vcs.git -> FileChange.source -> cr.ui.page_content row rendering
```

- `cr.vcs.git` owns the Git subprocess calls needed to determine source.
- `FileChange` carries the source fact alongside path/status/counts.
- `cr.ui.page_content` owns how that fact is displayed in Changed Files rows.

This keeps source detection out of the browser executor and avoids adding
another state source in `BrowserState`.

## Behavior Preservation

- Existing status values (`modified`, `added`, `deleted`, `renamed`,
  `untracked`) keep their lifecycle meaning.
- Source is orthogonal to lifecycle status.
- Command parsing, task panel, selected-file actions, and navigation stay
  unchanged.

## Risks / Trade-offs

- **Risk:** adding `source` to `FileChange` could leak mutable-local language
  into base/range review.
  **Mitigation:** only annotate local non-base/non-range scopes.

- **Risk:** row text could become noisy.
  **Mitigation:** render a compact single-word badge only when the source fact
  exists.

- **Risk:** extra Git calls could hurt very large repos.
  **Mitigation:** reuse lightweight `git diff --name-only` calls and only run
  source detection for local scopes.
