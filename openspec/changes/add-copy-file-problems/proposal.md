## Why
Task Problems can already group by file, but handoff actions are still either
one selected problem or the whole visible list. In real IDE-style build loops,
the useful middle step is often "copy every current problem in this file" so AI
or chat context stays focused without losing related diagnostics from the same
file.

## What Changes
- Add `copy file problems` for Task Problems.
- The command copies all currently visible problems with the same path as the
  selected problem.
- It respects existing severity, text query, and sort filters because it works
  from the current visible Problems list.
- Expose the command in help, action bar, command catalog, README, and P0 docs.

## Impact
- Affects Task Problems handoff only.
- Does not add quick-fix execution, diagnostics persistence, collapsible groups,
  or task-history browsing.
