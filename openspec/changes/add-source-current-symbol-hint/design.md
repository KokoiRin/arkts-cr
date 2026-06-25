## Context

`cr.source.outline` already provides coarse regex-based symbols for ArkTS/ETS/TS and is used by File Detail purpose/outline behavior. Source File Page intentionally stays a read-only preview owned by `cr.ui.source_file`; it should not parse syntax itself or become an editor.

## Goals / Non-Goals

**Goals:**

- Compute a readable current-symbol label for a target source line using existing outline symbols.
- Show that label in Source File Page header as a temporary render fact.
- Add the label to `copy source` Markdown for both context snippets and selected ranges.
- Gracefully omit the label when no symbol is found or the file cannot be parsed.

**Non-Goals:**

- No language server, AST parser, semantic indexing, or cross-file lookup.
- No syntax-aware range expansion or automatic function selection.
- No new Source File Page persistent state.
- No File Detail behavior change in this slice.

## Decisions

1. **Current symbol lookup belongs to `cr.source.outline`.**
   - The outline module already owns regex symbol facts, including line and end-line. Adding a pure lookup helper keeps parsing out of TUI modules.

2. **Source File Page receives a render fact, not new navigation state.**
   - Browser computes the label from the current file content and target line, then Page Content renders it. Back/forward snapshots do not need another state field because the label is derived.

3. **Copied source includes the same label.**
   - Handoff text benefits from the same context the user sees, but the copied code range remains unchanged.

## Risks / Trade-offs

- Regex symbols are best-effort and may miss complex syntax; the UI omits the label rather than showing `unknown`.
- Computing on render rereads/parses the current source file; this is acceptable for the first slice and avoids cache invalidation state.
- The label is informational only, so wrong/missing hints do not affect navigation or copy ranges.
