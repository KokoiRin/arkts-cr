## 1. Handoff Save Helpers

- [x] 1.1 Add a small UI handoff helper for default save paths, repo-relative/absolute path resolution, UTF-8 write, parent directory creation, and failure messages.
- [x] 1.2 Refactor browser prompt handoff generation so copy and save share selection, review-note filtering, review-data construction, and Markdown rendering.

## 2. Browser Commands

- [x] 2.1 Add `SAVE_PROMPT` and `SAVE_FILE_PROMPT` command actions and parse `save prompt [PATH]` / `save prompt file [PATH]`.
- [x] 2.2 Execute save prompt actions through `BrowserCommandExecutor`, preserving page, selection, scope, filters, notes, progress, and task state.
- [x] 2.3 Add command catalog entries for `save prompt` and `save prompt file`.

## 3. Tests And Docs

- [x] 3.1 Add focused tests for parser actions, command catalog discoverability, default save paths, explicit paths, selected-file save, empty scopes, write failures, and raw-key status feedback.
- [x] 3.2 Update README, `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`, and `docs/p0.md`.

## 4. Verification

- [x] 4.1 Run OpenSpec validation, targeted command/handoff tests, full unit tests, compile checks, diff checks, and Warden review.
