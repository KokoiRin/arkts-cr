## Context

The browser already has three filter surfaces:

- Changed Files path filter, owned by `ReviewWorkspace`.
- Changed Files source filter, also owned by `ReviewWorkspace`.
- Command Palette filter, owned by browser-local command palette state.

Commit Picker is another first-layer selector and needs the same direct filtering
ergonomics as an IDE history/log panel, but its filter must not reuse
Changed Files state.

## Goals / Non-Goals

**Goals:**
- Let `/`, `/QUERY`, and `filter QUERY` narrow loaded recent commits while Commit
  Picker is active.
- Match against hash, authored date, subject, and file/churn summary text.
- Keep numeric selection, Enter, paging, and refresh working against the
  filtered commit list.
- Make `c` / `clear` clear only the active Commit Picker filter.

**Non-Goals:**
- No Git re-query for server-side history search.
- No persisted commit filter in `.git/cr/browse-state.json`.
- No new Review Scope type.
- No change to Changed Files filtering or Command Palette filtering behavior.

## Decisions

1. Keep Commit Picker filter as browser-local UI state.

   Commit filtering is a temporary view over loaded commits, like Command
   Palette filtering. It should not enter `ReviewWorkspace`, which owns review
   scope and changed-file state.

2. Filter loaded commits in process.

   The current Commit Picker loads a bounded recent commit list. Filtering that
   list is fast, testable, and avoids introducing Git log search semantics as a
   separate feature.

3. Render filter context in Page Content.

   Page Content already owns Commit Picker rows and empty states. It should show
   match counts and no-match text without knowing command routing details.

## Risks / Trade-offs

- **Risk:** users may expect search beyond the loaded recent commit limit.
  **Mitigation:** keep this as a local filter over "Recent commits"; broader log
  search can be designed separately.

- **Risk:** adding another filter state grows `BrowserState`.
  **Mitigation:** keep it browser-local and avoid persistence. If Commit Picker
  grows further, it becomes a candidate for a deeper module.
