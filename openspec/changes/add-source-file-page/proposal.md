## Why

Task Problems can now extract build/test/lint file anchors, copy them, and open them in an external editor. For an IDE-like terminal workbench, the next missing loop is quickly reading the source around a problem without leaving the TUI. Build errors often point at files that are not changed in the current Review Scope, so File Detail is not enough.

## What Changes

- Add a Source File Page as a cross-layer read-only source preview.
- Add `view problem` for opening the selected Task Problems entry in Source File Page.
- Render repo-relative path, line numbers, and a target-line marker centered near the problem line.
- Support scrolling with existing movement keys and page history back/forward.
- Keep `Enter` on Task Problems as external editor open; `view problem` is the in-TUI read path.
- Do not add full-file editing, syntax highlighting, diagnostics persistence, task history search, or source-file workspace persistence.

## Capabilities

### New Capabilities

- `source-file-page`: read-only in-TUI source preview for repo-local files.

### Modified Capabilities

- `task-problems-page`: exposes `view problem` to inspect selected problem source in the TUI.
- `browser-page-navigation`: navigation stack supports Source File Page.
- `browser-command-dispatch`: parses `view problem`.

## Impact

- Adds a small source file view model for safe repo-local reads and windowing.
- Extends browser state/navigation/page content/command execution.
- Does not touch Git review facts, task runtime lifecycle, workspace persistence, or external editor handoff behavior.
