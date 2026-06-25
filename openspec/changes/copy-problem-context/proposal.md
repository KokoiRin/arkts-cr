## Why

Task Problems can already jump to source, copy a problem, and copy source context. The next handoff pain is combining those pieces with the current Review Scope diff so an AI/chat review can reason about the failing line and the actual local change without several manual copy steps.

## What Changes

- Add `copy problem context`.
- On Task Problems, copy selected problem facts, source context, and same-file diff if that file is changed in the current Review Scope.
- On Source File Page, copy current source target, source context, and same-file diff if available.
- Add command catalog/action bar/docs entries.

## Non-Goals

- No save command.
- No persistent diagnostics model.
- No cross-file dependency collection.
- No full prompt template or task-output transcript.
- No source editing or selection model.
