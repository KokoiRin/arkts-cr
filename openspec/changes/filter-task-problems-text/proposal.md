## Why

Severity filters and sorting help with broad triage, but real build/test output can still contain many errors in the same severity. Users need a quick way to narrow Task Problems by path, diagnostic code, or message without leaving the TUI or searching raw task output.

## What Changes

- Add `problems find TEXT` to filter current Task Problems by text.
- Add `problems clear find` to clear the text filter.
- Show the active query in the Task Problems header.
- Apply query filtering to rendered rows, movement, open/view, and copy actions.

## Non-Goals

- No regex syntax.
- No task history search.
- No source-file content search.
- No persistence across sessions.
- No changes to task output extraction.
