## Design

`Workspace Persistence` is a local-substitutable UI module. It owns file I/O and persistence schema knowledge, while `ReviewWorkspace` owns product state interpretation and `browser.py` owns session orchestration.

Current split:

- `ReviewWorkspace.state_data(...)`: produce product navigation state.
- `ReviewWorkspace.restore_state(...)`: interpret product navigation state.
- `Workspace Persistence`: choose file path, wrap version, read/write JSON, validate persisted shape, decide whether default startup should restore.
- `browser.py`: call load before building state, call save on exit, and apply restored state to the live `BrowserState`.

## Module Interface

The module should expose:

- `workspace_state_path(repo: Path) -> Path`
- `should_restore_workspace_state(args) -> bool`
- `should_save_workspace_state(args) -> bool`
- `workspace_state_data(workspace, args, mode) -> dict[str, object]`
- `save_workspace_state(workspace, args, repo, mode) -> None`
- `load_workspace_state(repo) -> dict[str, object] | None`
- `restore_workspace_scope(args, workspace_state) -> None`

`browser.py` may keep wrapper names such as `_save_browser_workspace_state` for compatibility, but the implementation should delegate.

## Behavior Preservation

This is an extraction, not a product change. Preserve:

- state file path: `.git/cr/browse-state.json`
- schema version: `1`
- tolerant save/load behavior: I/O and JSON errors do not crash browsing
- restore only for default browse sessions without explicit staged/all/base/range/untracked/path arguments
- do not save default workspace state on exit when path filters were supplied as CLI path arguments
- do not persist task runtime/history
- persist and restore scope, filter, selected path/index, list/file layer, progress markers, remaining-only mode, and review notes

## Non-Goals

- Do not change persisted schema.
- Do not add migration support.
- Do not persist task state or task history.
- Do not move terminal rendering or task panel rendering.
