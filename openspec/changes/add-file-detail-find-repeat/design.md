## Design

Add two parsed actions:

- `next match`
- `prev match`

`find TEXT` stores the trimmed non-empty query on `BrowserState` after command
execution. `next match` and `prev match` use that query and the current
`file_scroll`.

Search behavior:

- Search rendered File Detail body lines case-insensitively.
- Strip ANSI color codes before matching.
- For `next match`, search after the current `file_scroll`, then wrap to the
  beginning.
- For `prev match`, search before the current `file_scroll`, then wrap to the
  end.
- If there is no previous query, report that `find TEXT` must run first.
- If the stored query has no matches after content changes, keep scroll and
  report no matches.

## Module Boundaries

- `file_detail_navigation` owns repeat-match calculation over rendered lines.
- `BrowserState` owns session-local last File Detail find query.
- `browser.py` owns File Detail page checks, cached rendered-line retrieval,
  applying returned scroll, and status feedback.
- `Command Catalog` owns help/palette visibility.

## Non-Goals

- Do not use `n` / `p`; those remain next/previous file commands.
- Do not change `/` filtering behavior.
- Do not persist the search query in browse state.
- Do not highlight all matches yet.
- Do not search across files.

## Verification

- Unit tests cover next/previous match search including wraparound and empty
  query behavior.
- Browser executor tests cover `find TEXT` storing query, `next match`, `prev
  match`, missing prior query, and state preservation.
- OpenSpec strict validation, compile checks, diff checks, Warden review, and
  full unit tests must pass.
