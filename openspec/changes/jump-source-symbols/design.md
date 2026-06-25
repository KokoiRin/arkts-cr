## Design

`cr.source.outline` already exposes `parse_outline()` and `flatten_symbols()`.
The browser will use those existing facts to move within the current Source
File Page:

- `next symbol` selects the first recognized symbol whose start line is greater
  than the current `source_file_line`.
- `prev symbol` selects the nearest recognized symbol whose start line is less
  than the current `source_file_line`.
- On success the browser updates `source_file_line` and sets
  `source_file_scroll = -1`, matching the existing find/source navigation
  behavior that recenters the target line.
- On boundary or empty states the browser reports a clear message and preserves
  the current line.

## Boundaries

- Command parsing stays in `cr.ui.commands`.
- Source File Page state changes stay in `cr.ui.browser`.
- The outline module is reused unchanged.
- The command is page-scoped by behavior; parsing is global like other browser
  commands, but non-Source File pages get an explanatory message.

## Validation

- Parser tests cover `next symbol` and `prev symbol`.
- BrowserCommandExecutor tests cover jumping forward/backward, boundary
  messages, missing source file, and no-symbol files.
- Help/README/P0 docs describe the new commands.
