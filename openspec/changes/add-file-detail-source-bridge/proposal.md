# Add File Detail Source Bridge

## Why

File Detail is where users spend most review time reading diffs. After the
Source File page gained symbol hints and symbol-range selection, users still
need a quick bridge from a diff row to the read-only source preview. Today
`open line` leaves the TUI and opens an editor; `copy line` only copies an
anchor. Neither keeps the review workflow inside cr.

This P0 connects File Detail -> Source File so users can read surrounding source
and then reuse `source select symbol` / `copy source`.

## What Changes

- Add a File Detail command: `view source`.
- The command opens Source File at the current rendered new-file line.
- The command uses the same rendered-line mapping as `open line` and `copy line`.
- Document the command in File Detail help, command catalog, action bar, README,
  and P0 notes.

## Non-Goals

- No old-version source preview for deleted-only rows.
- No source editing.
- No language-service lookup.
- No automatic symbol selection.
- No File Detail layout redesign.
