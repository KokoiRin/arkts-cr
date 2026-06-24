## Context

The product hierarchy is:

```text
Review Scope / Commit
  -> Changed Files
    -> File Detail
```

Scope Home is the visible entry point for the first layer. It already exposes
Worktree, Staged, All local changes, Recent commits, Base ref, and Explicit
range. The missing information is a lightweight overview count for the scopes
that can be counted without user input.

## Goals / Non-Goals

**Goals:**
- Show file counts for Worktree, Staged, and All local changes.
- Show commit count for Recent commits.
- Respect existing path/code/untracked filters when counting changed files.
- Load counts when Scope Home is opened and when it is refreshed.
- Keep counts out of persisted workspace state.

**Non-Goals:**
- No inline input form for Base ref or Explicit range.
- No new Review Scope.
- No background polling or per-frame Git queries.
- No change to commit selection or Changed Files behavior.

## Decisions

1. Sample counts in `cr.ui.browser`.

   Browser orchestration already decides when pages open, refresh, and call Git
   through review-scope helpers. It should load Scope Home counts at those
   product events instead of making `page_content` perform subprocess work.

   Alternative considered: compute counts during render. That would make screen
   redraws slower and blur the rendering boundary.

2. Render counts in `cr.ui.page_content`.

   Page Content owns Scope Home row text. It can format counts from a simple
   dictionary on state without knowing how those counts were loaded.

   Alternative considered: pre-format labels in `browser.py`. That would split
   row presentation between orchestration and rendering.

3. Keep counts as non-persisted UI state.

   Counts are a snapshot for the visible overview, not user-authored workspace
   data. They can be refreshed by reopening Scope Home or pressing refresh
   while on Scope Home.

## Risks / Trade-offs

- **Risk:** counts can become stale while the user stays on Scope Home.
  **Mitigation:** `r` refreshes Scope Home counts, and reopening Scope Home
  reloads them.

- **Risk:** opening Scope Home now runs several Git queries.
  **Mitigation:** queries happen only on page entry/refresh, not on every frame
  redraw.

- **Risk:** Git count loading can fail outside a valid repository.
  **Mitigation:** failed counts are omitted; existing navigation behavior
  remains available.
