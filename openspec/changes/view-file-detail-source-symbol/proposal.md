# Change: view-file-detail-source-symbol

## Why

File Detail is where users read changed hunks, but when a changed line needs fuller source context the current flow is two steps: `view source`, then `source select symbol`. That slows the main AI review loop when the user wants to inspect or hand off the enclosing function/method around a diff row.

## What Changes

- Add `view source symbol` as a TUI command.
- From File Detail, it opens Source File at the current new-file line and selects the enclosing lightweight source symbol.
- If the current diff row has no new-file line, keep the user on File Detail and show the existing no-line error.
- If the source line has no recognized symbol, keep the opened Source File focused on the line but report that no symbol was selected.

## Non-Goals

- No source editing, quick fixes, language server, outline panel, or cross-file dependency expansion.
- No new persisted state beyond the existing Source File selection fields.
- No business-repo-specific behavior.
