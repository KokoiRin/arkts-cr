## Context

Changed Files currently owns three related source-control surfaces:

- `cr.vcs.git.FileChange.source` carries local facts: `staged`, `unstaged`, or
  `mixed`.
- Changed Files rows render those facts as compact badges.
- `ReviewWorkspace.source_filter` can narrow the visible list by one source.

The missing piece is an overview. The summary should answer "what source mix am
I looking at right now?" without adding another navigation level or another Git
query.

## Goals / Non-Goals

**Goals:**
- Show source counts for the current rendered Changed Files set.
- Keep the summary derived from existing `FileChange.source` facts.
- Keep comparison scopes badge-free and summary-free when no source facts exist.
- Preserve existing path filter, source filter, remaining-only, and row behavior.

**Non-Goals:**
- No new Review Scope.
- No source grouping or sorting.
- No new command.
- No new Git subprocess calls.
- No `cr review` or `cr diff` output changes.

## Decisions

1. Put the summary in `cr.ui.page_content`.

   `Page Content` already owns Changed Files header text and row rendering. A
   source summary is display-only metadata derived from the list being rendered,
   so it should not become persisted workspace state.

   Alternative considered: store counts in `ReviewWorkspace`. That would create
   another state source for data that can be recomputed cheaply from
   `visible_changes`.

2. Count the current rendered changes.

   The summary should reflect the same list shown below it, including any active
   path filter, source filter, or remaining-only view. This keeps the text easy
   to explain and avoids passing parallel unfiltered lists into rendering.

   Alternative considered: always show counts for the unfiltered review scope.
   That would be useful for navigation, but it would make the header disagree
   with filtered rows unless the renderer accepted additional scope data.

3. Omit zero and unknown source values.

   Only `staged`, `unstaged`, and `mixed` are user-facing local source labels.
   Unknown or empty values should not show in the summary. If all rendered
   changes lack source facts, no source summary should be printed.

## Risks / Trade-offs

- **Risk:** an active `source staged` filter may show only `Sources: staged N`,
  which is confirmatory rather than navigational.
  **Mitigation:** this still accurately describes the rendered list and keeps
  the implementation local. A later scope-wide overview can be designed
  separately if usage demands it.

- **Risk:** adding a header line reduces visible row capacity in small
  terminals.
  **Mitigation:** only render the summary when local source facts exist, and let
  existing scroll-window logic absorb the extra line.
