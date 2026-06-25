# Add Source File Symbol Selection

## Why

After `view problem` opens a Source File page, users often need to hand off the
whole enclosing method or function to AI. Today they can copy nearby context,
manually select line ranges, or mark/select to the current line, but choosing a
method block still requires reading line numbers and typing them by hand.

This P0 shortens the Problems -> Source File -> Handoff loop by letting users
select the current symbol range with one command.

## What Changes

- Add a Source File command: `source select symbol`.
- On Source File, the command selects the innermost best-effort outline symbol
  containing the current source line.
- The existing `copy source` command then copies that selected range, including
  the existing `Symbol: ...` metadata.
- Document the command in page help, command catalog, action bar, README, and
  P0 notes.

## Non-Goals

- No language-server dependency.
- No complete ArkTS/TypeScript parser.
- No source editing.
- No cross-file selection.
- No automatic copy side effect.
- No File Detail behavior change.
