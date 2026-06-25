## Why

Task Problems can filter, sort, search, open, and hand off diagnostics, but large
outputs still scan like a flat log-derived list. Users need a file-level visual
grouping so they can quickly see which files dominate the current problem set
without leaving the Problems page.

## What Changes

- Add `problems group file` to render Task Problems grouped by file path.
- Add `problems group none` to return to the existing flat rendering.
- Show active grouping in the Task Problems header.
- Keep selection, Enter/open, `view problem`, `copy problem`, `copy problems`,
  and `copy problem context` operating on the same visible problem list.

## Non-Goals

- No collapsible groups.
- No group-level selection or bulk actions.
- No persisted grouping preference.
- No tool-specific diagnostics hierarchy.
- No change to extraction, severity filters, text query, or sorting semantics.
