## Design

`cr.ui.source_file` already owns pure source reading and snippet formatting through `source_context_markdown(content, target_line, context_lines=3)`. Browser state owns Source File Page path, target line, scroll, and find text. The adjustable radius follows that split:

- `BrowserState.source_context_lines` stores the page-local radius.
- `BrowserNavigation` snapshots and restores it with Source File Page history.
- `BrowserCommandAction.SET_SOURCE_CONTEXT_LINES` represents `source context N`.
- Browser Action Execution validates and applies the command.
- `copy source` passes the active radius into `source_context_markdown`.
- Page Content renders the active radius in the Source File Page header.

## Behavior

`source context N` accepts a non-negative integer. The implementation clamps large values to a small upper bound so accidental input cannot copy a huge source file from a tall terminal workflow. The default remains 3, preserving existing behavior until the user opts in.

The radius is not persisted to `.git/cr/browse-state.json`. It belongs to the current Source File Page session just like source scroll and find state.

## Boundaries

This change deliberately avoids building a selection model. A future richer selection can still add explicit start/end lines without invalidating this smaller radius setting.
