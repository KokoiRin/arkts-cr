## Why

File Detail now supports hunk navigation, editor handoff, copy, and refresh
preservation, but users still cannot search within the currently inspected
file detail. IDE review workflows frequently require jumping to a symbol,
property, or changed text inside the current file without leaving the view.

## What Changes

- Add `find TEXT` as a File Detail command.
- Search the current rendered File Detail lines case-insensitively.
- Jump `file_scroll` to the first matching rendered body line.
- Report clear status for outside File Detail, empty queries, and no matches.

## Impact

- Improves File Detail ergonomics without changing `/` path/filter behavior.
- Keeps search local to the current selected file and current Review Scope.
- Does not add full-repository search or persistent search state.
