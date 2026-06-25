## Why

Task Problems currently extract repo-local `path:line[:column]` anchors from build/test/lint output, but every row is still a raw log line. As the TUI grows toward IDE replacement, the Problems page needs basic diagnostics facts so users can scan error vs warning, copy richer handoff text, and decide what to open first without reading full logs.

## What Changes

- Extend `TaskProblem` with optional diagnostic facts: severity, code, and message.
- Extract common severity words near a problem anchor: error, warning/warn, info, and note.
- Extract common diagnostic codes near the severity/message area, such as `TS2322`, `[E123]`, or `W001`.
- Render the Problems page with a compact diagnostic label when facts are present.
- Include diagnostic facts in `copy problem` / `copy problems` handoff text.

## Scope

- `task-problems-diagnostics`: lightweight enrichment of already extracted task problems.

## Non-Goals

- No tool-specific parser registry.
- No severity sorting or filtering.
- No diagnostics persistence or history search.
- No changed-file integration.
- No source snippet extraction.
