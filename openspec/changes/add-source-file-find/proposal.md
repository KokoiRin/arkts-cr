## Why

Source File Page lets users inspect source around a task problem without leaving the TUI. The next IDE-like operation is searching that read-only source preview for a symbol or nearby text. Without search, users must scroll manually through files that may be much larger than the initial problem window.

## What Changes

- `find TEXT` works on Source File Page.
- `next match` and `prev match` repeat the last Source File Page query with wraparound.
- Matches update the Source File Page target line and scroll so the matched source line is visible.
- Source File Page keeps its own `source_find_text`, separate from File Detail and Task Output find state.
- No syntax parsing, highlighting, editing, source persistence, diagnostics parsing, or task history search is added.

## Capabilities

### New Capabilities

- `source-file-find`: search within the current read-only Source File Page.

### Modified Capabilities

- `source-file-page`: supports text find and repeated match navigation.
- `browser-command-dispatch`: existing find commands apply to Source File Page.

## Impact

- Extends Source File Page state with source-specific find text.
- Reuses `cr.ui.text_search` for case-insensitive plain-text matching.
- Extends browser action execution and contextual action text.
- Does not touch task runtime, Git review facts, workspace persistence, or editor handoff behavior.
