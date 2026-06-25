## Design

Add a `find TEXT` browser command that maps to a new parsed action. The browser
executor handles page validation and cached File Detail line retrieval, then
delegates rendered-line matching to `cr.ui.file_detail_navigation`.

Search behavior:

- Trim the query after `find`.
- Match case-insensitively against rendered File Detail body lines.
- Strip ANSI color codes before matching.
- Treat `file_scroll` as a body-line index and set it to the first matching
  body line.
- Return a status message such as `Found "query" at line N.` where `N` is the
  1-based rendered body line.

## Module Boundaries

- `BrowserCommandAction` owns command parsing vocabulary.
- `Command Catalog` owns command help/palette visibility.
- `file_detail_navigation` owns rendered File Detail line search rules.
- `browser.py` owns page checks, cached File Detail line retrieval, state
  mutation, status feedback, and redraw.

## Non-Goals

- Do not change `/` behavior; `/` remains a filter/search prompt for the active
  page's existing filter model.
- Do not add global repository search.
- Do not persist search query state.
- Do not highlight matches yet.
- Do not add next/previous match commands yet.

## Verification

- Unit tests cover rendered File Detail matching and no-match behavior.
- Browser executor tests cover File Detail success, outside-File Detail status,
  empty query status, no-match status, and state preservation.
- OpenSpec strict validation, compile checks, diff checks, Warden review, and
  full unit tests must pass.
