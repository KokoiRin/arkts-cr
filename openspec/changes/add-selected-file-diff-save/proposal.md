## Why

`copy diff` is useful when the terminal clipboard works, but the same selected
file diff snippet should also be available in environments where clipboard
handoff is unreliable or the user wants to keep a durable review artifact.

This change adds `save diff [PATH]` as the file-backed counterpart to
`copy diff`.

## What Changes

- Add `save diff [PATH]` command parsing and command catalog entry.
- Save the current selected file's compact Markdown diff snippet to disk.
- Default to `.cr/handoff/review-diff.md` when no path is supplied.
- Preserve page, selection, scope, filters, notes, progress, and task state.
- Surface empty-selection and file-write failures as status messages.

## Capabilities

### New Capabilities

- `selected-file-diff-save`: users can save the selected file's compact diff
  review snippet from the browser.

### Modified Capabilities

无。

## Impact

- Updates browser command parsing, command catalog, selected-file action
  execution, and UI-side handoff writes.
- Updates README and architecture/product docs.
- Adds focused parser, handoff, action, and executor tests.
