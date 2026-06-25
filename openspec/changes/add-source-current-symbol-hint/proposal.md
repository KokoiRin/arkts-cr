## Why

After `view problem`, users land in Source File Page and need to quickly understand which class, method, or function the failing line belongs to. The page already supports find, range selection, and source context handoff, but users still have to infer the enclosing symbol from surrounding code.

A small current-symbol hint improves reading and AI handoff without introducing a full language service or syntax-aware selection model.

## What Changes

- Show a best-effort current symbol label in the Source File Page header when the target line falls inside a parsed symbol.
- Include the same symbol label in copied source context/range Markdown.
- Reuse the existing regex-based `cr.source.outline` parser.
- Keep Source File Page read-only and avoid new persisted state.

## Capabilities

### New Capabilities
- `source-current-symbol-hint`: expose best-effort enclosing symbol context for Source File Page reading and source handoff.

## Impact

- Touches `cr.source.outline` for a pure current-symbol lookup helper.
- Touches `cr.ui.source_file` for source Markdown symbol metadata and view facts.
- Touches `cr.ui.page_content` and `cr.ui.browser` for rendering/routing the label.
- No task runtime, Git scope, Problems parser, workspace persistence, or editor handoff changes.
