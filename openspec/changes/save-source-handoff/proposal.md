# Save Source Handoff

## Why

`copy source` and `copy source symbol` create the right minimal source handoff, but clipboard-only workflows are fragile in remote terminals and long AI sessions. Users need the same source snippets as durable Markdown files without inflating them into full problem context.

## What Changes

- Add `save source [PATH]` for the same Markdown produced by `copy source`.
- Add `save source symbol [PATH]` for the same Markdown produced by `copy source symbol`.
- Support both Source File and File Detail where the matching copy commands already work.
- Use defaults under `.cr/handoff`.

## Non-Goals

- No source editing.
- No language-server lookup.
- No cross-file dependency collection.
- No automatic symbol selection side effects.
- No change to `copy problem context` or problem context defaults.
