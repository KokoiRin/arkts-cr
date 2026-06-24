## Why

`refresh` currently reloads changed files and always returns to Changed Files.
That is safe, but it breaks the IDE-like workflow when a user is reading a File
Detail page and wants to reload after edits, build output, or Git index changes.

An IDE-style workbench should preserve the current editing/review context when
the selected file is still part of the refreshed Review Scope.

## What Changes

- Preserve File Detail on ordinary `refresh` when the selected file still
  exists in the refreshed visible changes.
- Preserve the selected path and clamp File Detail scroll after re-rendering.
- Return to Changed Files when the selected file disappears from the refreshed
  scope.
- Keep stage/unstage refresh behavior unchanged: successful index actions still
  return to Changed Files.

## Impact

- Improves long-running terminal workbench ergonomics.
- Keeps Review Scope reload and selected-file state ownership aligned with
  `ReviewWorkspace`.
- Does not change command syntax, filtering, source filtering, or task panel
  behavior.
