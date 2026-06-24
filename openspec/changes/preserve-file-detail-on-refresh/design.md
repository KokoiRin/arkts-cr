## Design

Add a refresh path for ordinary `refresh` command execution:

1. Capture whether the current page is File Detail, the selected path, and the
   current `file_scroll`.
2. Reload changed files for the current Review Scope.
3. Let `ReviewWorkspace` restore selection by the previously selected path when
   possible.
4. Clear rendered File Detail caches.
5. Reset page history for the reloaded scope.
6. If the selected path still exists in visible changes, keep File Detail and
   clamp `file_scroll` to the newly rendered file height.
7. Otherwise show Changed Files and report that the current file is no longer
   changed.

## Module Boundaries

- `ReviewWorkspace` owns changed-file reload and selected-path restoration.
- `browser.py` owns page preservation, File Detail cache invalidation, scroll
  clamping, status feedback, and redraw.
- `BrowserNavigation` keeps transition primitives; ordinary refresh should not
  create a synthetic back-stack entry.
- Stage/unstage keeps using the existing action-refresh path, which returns to
  Changed Files after a mutating index operation.

## Non-Goals

- Do not preserve File Detail across explicit Review Scope switches.
- Do not preserve File Detail after stage/unstage.
- Do not add a new command or key binding.
- Do not change filter/source filter semantics.

## Verification

- Unit tests cover File Detail preservation when the selected path survives.
- Unit tests cover fallback to Changed Files when the selected path disappears.
- Existing tests cover refresh history reset and stage/unstage refresh behavior.
- OpenSpec strict validation, compile checks, diff checks, Warden review, and
  full unit tests must pass.
