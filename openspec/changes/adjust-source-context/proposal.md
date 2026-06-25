## Why

Source File Page can already preview source around a task problem and copy a fixed nearby snippet. In real review and AI handoff loops, a fixed three-line radius is sometimes too narrow for type/lifecycle context and sometimes too noisy for a small syntax failure.

## What Changes

- Add a page-local Source File Page context radius used by `copy source`.
- Add `source context N` to set the current radius.
- Keep the default radius at 3 lines.
- Show the active radius on Source File Page.

## Non-Goals

- No interactive multi-line selection.
- No cross-file snippets.
- No syntax-aware expansion.
- No session persistence.
- No editing behavior.
