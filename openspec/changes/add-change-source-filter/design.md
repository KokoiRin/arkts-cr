## Context

Changed Files already supports path filtering and remaining-only filtering. The
new source filter should live in the same product layer:

```text
Review Scope
  -> Changed Files [path filter + source filter + remaining filter]
    -> File Detail
```

It is not a new Review Scope. `staged` and `worktree` remain top-level scopes;
`source staged` is a temporary view filter inside the current scope, most useful
inside `all local changes`.

## Requirement Card

## Requirement

Implement source filtering for Changed Files in `cr browse`.

## Expected Behavior

- `source staged` shows visible changes whose `FileChange.source == "staged"`.
- `source unstaged` shows visible changes whose `FileChange.source == "unstaged"`.
- `source mixed` shows visible changes whose `FileChange.source == "mixed"`.
- `source all` and `source clear` clear the source filter.
- Source filtering composes with path filter and remaining-only filtering.
- Changed Files header shows the active source filter.
- Scope switching and restore-to-workspace scope clear the source filter.

## Not Doing

- No new Git calls.
- No source grouping or new page.
- No source filter in `cr review` or `cr diff`.
- No new sorting mode.
- No persistent behavior outside the existing browser workspace state.

## Acceptance Criteria

- Workspace visible changes apply source filtering after path filtering and
  before remaining-only filtering.
- Command parser recognizes source filter commands.
- Command palette lists executable source filter commands.
- Browser executor applies/clears source filter without changing scope, task
  state, notes, or progress markers.
- Header text shows the active source filter.

## Module Shape

Dependency category: in-process state.

The useful module path is:

```text
BrowserCommandAction -> BrowserCommandExecutor -> ReviewWorkspace.source_filter
                                            -> Page Content header rendering
```

- `cr.ui.commands` owns command parsing.
- `ReviewWorkspace` owns the filter state and visible-change rules.
- `cr.ui.page_content` owns display text.
- `BrowserCommandExecutor` mutates state and requests redraw.

## Behavior Preservation

- Existing `/QUERY` path filtering remains unchanged.
- `remaining` continues to filter after the path/source-filtered set.
- `allfiles` clears only remaining-only mode, not path/source filters.
- `clear` continues to clear the active path filter, or command filter inside
  Command Palette.

## Risks / Trade-offs

- **Risk:** `source staged` can be confused with the `staged` Review Scope.
  **Mitigation:** the explicit `source` prefix makes it a view filter; the
  existing `staged` command remains a scope switch.

- **Risk:** comparison scopes have no source values, so source filters can show
  empty lists.
  **Mitigation:** this is consistent with other filters; users can clear it with
  `source all`.
