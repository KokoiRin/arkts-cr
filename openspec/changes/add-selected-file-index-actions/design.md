## Context

The product hierarchy is:

```text
Review Scope
  -> Changed Files
    -> File Detail
```

Staging and unstaging are not new review hierarchy layers. They are operations
on the currently selected file inside Changed Files / File Detail. That keeps
them aligned with existing selected-file actions such as `open`, `copy path`,
`copy anchor`, `reveal`, notes, and selected-file prompt handoff.

## Requirement Card

## Requirement

Implement selected-file `stage` and `unstage` commands in `cr browse`.

## Expected Behavior

- Input: the currently selected visible changed file.
- Output: a browser status message.
- Successful `stage`: runs `git add -- <path>` and refreshes the current Review
  Scope.
- Successful `unstage`: runs `git restore --staged -- <path>` and refreshes the
  current Review Scope.
- Empty selection: reports a missing-file message and does not run Git.
- Read-only scopes (`base REF`, `range OLD..NEW`, selected commit): report that
  index actions are only available for local worktree/index scopes.
- Git failure: reports the Git error and does not refresh.

## Not Doing

- No batch stage/unstage.
- No discard/revert/delete operation.
- No new page or Task Panel behavior.
- No attempt to mutate historical commit/base/range scopes.

## Acceptance Criteria

- `stage` and `unstage` parse into stable browser actions.
- Both actions appear in the executable command palette.
- Successful actions call Git through `cr.vcs.git`, refresh current changes, and
  clear stale file-detail render cache.
- Failure and empty-state paths preserve page state and selection.

## Module Shape

Dependency category: local Git subprocess boundary.

The useful seam is:

```text
BrowserCommandExecutor -> Selected File Actions -> cr.vcs.git
```

- `cr.vcs.git` owns subprocess calls and concise Git errors.
- `cr.ui.selected_file_actions` owns selected-file workflow messages and
  read-only-scope gating.
- `BrowserCommandExecutor` owns Browser Frame status placement and post-success
  workspace refresh.

This keeps index mutations out of command parsing, page rendering, and terminal
input code.

## Behavior Preservation

- Existing file actions keep their messages and command aliases.
- `refresh` remains the general manual reload command.
- Review Scope switching behavior stays unchanged.
- Task Panel lifecycle is untouched.

## Risks / Trade-offs

- **Risk:** after staging a file in worktree scope, the selected file may
  disappear from the visible list.
  **Mitigation:** refresh via the same path as `refresh`, clamp selection, and
  keep the user in Changed Files.

- **Risk:** `unstage` on an untracked or unstaged-only file can fail.
  **Mitigation:** let Git be authoritative and surface the Git error concisely.

- **Risk:** users may expect stage from a `base` or commit scope.
  **Mitigation:** keep those scopes read-only because they are comparisons, not
  mutable index views.
