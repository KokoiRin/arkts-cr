## Design

Command palette organization stays inside `browser.py` for now because the command catalog, palette rendering, selection, and execution already live there. This change should not introduce a new command registry module yet; the real pressure is search organization, not ownership extraction.

Filtering should compute two things from the same catalog:

- `entries`: all executable commands in normal palette order.
- `matches`: filtered entries sorted by match quality.

Match quality:

1. exact command or label match
2. command or label prefix match
3. command or label substring match
4. group match
5. description match

Ties preserve original palette order. Unfiltered mode preserves original palette order exactly.

## Rendering

When a filter is active, the palette shows:

```text
Filter: build (2/28 matches)
```

For empty results:

```text
Filter: zz-missing (0/28 matches)
No matching commands.
```

This gives users immediate feedback without adding a new page, modal, or help screen.

## Non-Goals

- Do not add fuzzy matching.
- Do not add aliases beyond existing command parser aliases.
- Do not change command execution semantics.
- Do not move the command catalog into a new module in this change.
- Do not make parameterized commands executable from raw palette.
