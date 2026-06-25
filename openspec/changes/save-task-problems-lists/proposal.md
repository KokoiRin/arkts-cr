# Save Task Problems Lists

## Why

`copy problems` and `copy file problems` are useful, but clipboard handoff is fragile in remote terminals and long build logs. Users need the same focused Problems list handoff as durable Markdown files without jumping through full problem-context generation for every diagnostic.

## What Changes

- Add `save problems [PATH]` to save the current visible Task Problems list.
- Add `save file problems [PATH]` to save visible problems for the selected problem's file.
- Use defaults under `.cr/handoff`.
- Preserve current filters, sorting, grouping, page, selection, and task state.

## Non-Goals

- No diagnostics persistence.
- No task history browsing.
- No parser changes.
- No batch source/diff context expansion.
- No quick fixes or source editing.
