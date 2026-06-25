## Context

File Detail already owns diff-specific line actions through selected-file workflows. Source File Page is different: it is a read-only repo-local source preview that can point at files outside Changed Files, and its current location is the `source_file_line` target marker.

## Decisions

1. Reuse `copy line`.
   - Reason: users should not learn a second command for the same "copy current line anchor" intent.
2. Copy only `path:line`.
   - Reason: this matches File Detail `copy line` and keeps source snippets separate from future richer handoff commands.
3. Keep implementation in Browser Action Execution.
   - Reason: the action needs page dispatch and clipboard side effects; `cr.ui.source_file` should stay a read-only loading/windowing model.

## Behavior

- On Source File Page with `source_file_path="src/Foo.ets"` and `source_file_line=20`, `copy line` copies `src/Foo.ets:20`.
- If Source File Page has no source path, `copy line` reports an empty state.
- The command does not change page, scroll, selection, task state, or review scope.

## Risks

- `copy line` now has page-specific behavior. The action bar and docs must make the active-page meaning visible enough to avoid confusion.
