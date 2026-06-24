## Why

`stage` and `unstage` make `cr browse` closer to an IDE source-control panel,
but the Changed Files list still does not say whether a local file is currently
staged, unstaged, or has changes on both sides of the index. After staging or
unstaging a file, users need a quick visual confirmation without switching
scopes.

## What Changes

- Attach a lightweight local change source to `FileChange` facts:
  - `staged`
  - `unstaged`
  - `mixed`
- Show the source badge in browser Changed Files rows.
- Keep base/range/commit comparison scopes free of local index badges.
- Preserve existing diff, review, JSON, filtering, sorting, and status behavior.

## Capabilities

### New Capabilities

- `browser-change-source-badges`: shows local index/worktree source badges in
  the browser Changed Files list.

### Modified Capabilities

无。

## Impact

- Touches `src/cr/vcs/git.py` to annotate local `FileChange` facts with source.
- Touches `src/cr/ui/page_content.py` for Changed Files row rendering.
- Adds focused Git fact and browser row tests.
- Updates product and architecture docs.
