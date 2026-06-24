## Why

Review Notes are now a stable browser workspace concept: users can set notes,
view summaries, filter notes, copy all notes, copy filtered notes, and include
notes in prompt/diff handoff. The summary/search/copy rules still live as
private helpers in `browser.py`, so the browser orchestration module owns too
much of the product model.

This change extracts Review Notes summary/search/copy behavior into a dedicated
`cr.ui.review_notes` module without changing user-visible commands.

## What Changes

- Add `cr.ui.review_notes` for note summary lines, filtering, ordering, and copy
  messages.
- Make `BrowserCommandExecutor` delegate `notes` and `copy notes` behavior to
  the module through browser compatibility wrappers.
- Preserve all existing command output, status feedback, page state, selection,
  scope, filters, and task behavior.
- Update architecture docs to name Review Notes as a UI module-owned surface.

## Capabilities

### New Capabilities

- `browser-review-notes-module`: Review Notes summary/search/copy rules are
  owned by a dedicated UI module.

### Modified Capabilities

无用户可见能力变化。

## Impact

- Adds `src/cr/ui/review_notes.py`.
- Updates `src/cr/ui/browser.py` to delegate note summary/copy behavior.
- Adds focused module tests and keeps browser behavior tests passing.
- Updates product and architecture docs.
