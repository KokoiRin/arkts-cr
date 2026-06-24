## Context

The browser already has a command language (`cr.ui.commands`), action execution (`BrowserCommandExecutor`), and an editor opener (`open`). File actions should deepen that existing model: commands parse to actions, the executor applies them to the selected changed file, and the browser status line reports the result.

## Goals / Non-Goals

**Goals:**

- Support `copy path`, `copy anchor`, and `reveal` for the selected changed file.
- Use the current review scope when resolving first changed lines for anchors.
- Keep feedback inside the existing browser message/status mechanism.
- Keep command palette entries executable and searchable.

**Non-Goals:**

- Do not add a visual file action menu.
- Do not add per-project file action configuration.
- Do not persist action history.
- Do not change `open` behavior.
- Do not implement multi-select actions.

## Decisions

### 1. Keep `open` as editor handoff

`open` already opens the selected file at the first changed line through `--open-cmd`, `CR_OPEN_CMD`, or editor defaults. This remains the editor-focused action.

### 2. Add explicit copy actions

`copy path` copies the repo-relative Git path, while `copy anchor` copies `path:line` when a first changed line exists. This gives users both a lightweight path and a precise review anchor.

### 3. Reveal uses the OS file browser

`reveal` locates the selected file in the OS file browser when supported. On macOS this maps to `open -R`; other platforms use common file-browser fallbacks when available.

### 4. Side effects stay behind helpers

Clipboard and reveal subprocess details should sit behind small helpers so the command executor remains about product actions, not platform probes.

## Risks / Trade-offs

- [Risk] Clipboard tools may be unavailable in some terminals. -> Mitigation: report a clear "No clipboard command found" message without failing the browser.
- [Risk] Reveal support differs by platform. -> Mitigation: use small platform-specific fallbacks and report missing support.
- [Risk] Adding too many aliases can make raw-key mode noisy. -> Mitigation: keep raw direct aliases minimal; primary usage is through `:` and the command palette.
