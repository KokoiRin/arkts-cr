## Why

Changed Files can already show `staged`, `unstaged`, and `mixed` badges per row,
and can filter by source, but the user still has to scan the whole tree to know
the current source mix. A source-control panel should expose that overview near
the changed-file count.

## What Changes

- Add a Changed Files source summary line derived from visible
  `FileChange.source` values.
- Show non-zero `staged`, `unstaged`, and `mixed` counts in a stable order.
- Omit the source summary when the rendered changes do not carry local source
  facts, such as base/range/commit comparison scopes.

## Capabilities

### New Capabilities
- `browser-change-source-summary`: displays local source counts for the current
  Changed Files view.

### Modified Capabilities
- None.

## Impact

- Touches `cr.ui.page_content` for Changed Files header/body rendering.
- Adds focused rendering tests for source summary behavior.
- Updates product and architecture docs for the new Changed Files metadata.
