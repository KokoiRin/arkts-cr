# File Detail Problem Stepping

## Why

After build/test/lint output is parsed into Problems, users can step problems in Task Output and Source File. File Detail is still the main diff-reading page, but `next problem` / `prev problem` there does not move the diff view to the relevant problem line. Users have to bounce through Task Problems or Source File just to inspect the changed hunk near a failure.

## What Changes

- In File Detail, `next problem` and `prev problem` select the next/previous parsed task problem for the current changed file.
- When the problem line is visible in the current file diff, File Detail scrolls to that rendered row.
- When the problem belongs to the current file but its line is not visible in the diff, File Detail keeps the page open and reports the selected problem line.

## Non-Goals

- No automatic cross-file switching.
- No synthetic diffs for unchanged lines.
- No new diagnostics persistence, source editing, quick fixes, language server, or multi-select problem workflow.
