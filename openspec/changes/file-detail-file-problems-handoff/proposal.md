# File Detail File Problems Handoff

## Why

`copy file problems` and `save file problems` are useful for handing all diagnostics for one file back to AI. In Task Problems, "current file" naturally means the selected problem's file. In File Detail, however, the current file is the changed file being reviewed. Today the commands still use the globally selected task problem, so File Detail can copy/save another file's problems while the user is reading a different diff.

## What Changes

- In File Detail, `copy file problems` and `save file problems [PATH]` scope to the current changed file.
- Task Problems and Task Output keep their existing selected-problem-file behavior.
- If the current File Detail file has no parsed task problems, report that no task problems exist for the current file.

## Non-Goals

- No new problem parser.
- No diagnostics persistence.
- No batch source/diff expansion.
- No source editing, quick fixes, language-server lookup, or cross-file dependency expansion.
