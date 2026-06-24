## Why

`cr browse` already supports copying a selected file path, anchor, review notes,
and AI-oriented prompt handoff. A frequent IDE-like workflow is lighter: copy
the current file's review diff snippet and paste it into chat, a PR comment, or
a task note without carrying the full handoff prompt.

This change adds `copy diff` as a selected-file action. It copies a compact
Markdown snippet for the current selected changed file, using the same review
facts and hunk context as the browser.

## What Changes

- Add a review snippet renderer for one selected file.
- Add `copy diff` command parsing, command palette entry, and browser execution.
- Reuse existing selected-file action and copy command configuration.
- Preserve page, selection, scope, filters, notes, progress, and task state.
- Surface empty-selection and copy-command failures as status messages.

## Capabilities

### New Capabilities

- `selected-file-diff-copy`: users can copy the selected file's compact diff
  review snippet from the browser.

### Modified Capabilities

无。

## Impact

- Adds `src/cr/review/snippet.py`.
- Updates browser command parsing, command catalog, and selected-file action
  execution.
- Updates README and architecture/product docs.
- Adds focused renderer, parser, action, and executor tests.
