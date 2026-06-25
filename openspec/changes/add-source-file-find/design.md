## Context

File Detail and Task Output already support `find TEXT`, `next match`, and `prev match` with page-local find state. Source File Page should follow the same command vocabulary while remaining a read-only source preview.

## Goals / Non-Goals

**Goals:**

- `find TEXT` searches the current Source File Page source lines.
- Search is case-insensitive and uses plain text.
- The first match becomes the Source File Page target line.
- `next match` / `prev match` repeat the last source query with wraparound.
- Searching unreadable or missing source reports an empty/error state without crashing.

**Non-Goals:**

- No syntax-aware search.
- No inline match highlighting.
- No search across files, TaskRecord history, or Review Scope.
- No persisted source find state.
- No editing or diagnostics parsing.

## Decisions

1. **Reuse existing command vocabulary.**
   - Choice: `find TEXT`, `next match`, and `prev match`.
   - Reason: users already learn these commands from File Detail and Task Output.

2. **Source find state is page-local.**
   - Choice: add `source_find_text` to `BrowserState` and page snapshots.
   - Reason: Source File Page should not overwrite File Detail or Task Output find queries.

3. **Matching updates target line.**
   - Choice: set `source_file_line` to the matched source line and center the next render around it.
   - Reason: the target-line marker is the Source File Page's current location concept.

## Risks / Trade-offs

- **No highlighting yet**: line-level movement is enough for this P0; highlighting can come after real use.
- **Repeated reads**: the page already reads UTF-8 text for preview. Search reuses the same lightweight model and can be optimized later if large files become a real problem.
