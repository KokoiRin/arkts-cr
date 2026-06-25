## Why

`find TEXT` can jump to the first rendered match in File Detail, but repeated
search is still missing. In an IDE-like review flow, users need to move between
multiple occurrences in the current file without retyping the query or leaving
File Detail.

## What Changes

- Add `next match` and `prev match` commands for File Detail.
- Remember the last non-empty File Detail find query for the current browser
  session.
- Search forward/backward from the current File Detail scroll and wrap within
  the current rendered file.
- Keep existing `n` / `p` file navigation and `/` filtering behavior unchanged.

## Impact

- Makes File Detail text search usable for repeated navigation.
- Keeps search local to the current selected file and current Review Scope.
- Adds only browser-session state; no workspace persistence changes.
