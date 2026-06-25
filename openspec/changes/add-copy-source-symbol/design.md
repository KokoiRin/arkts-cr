# Design

## Command Shape

New command:

- `copy source symbol`

Aliases:

- `copy symbol`
- `copy current symbol`

## Behavior

### Source File

1. Load the current source file content.
2. Parse the best-effort outline.
3. Find the symbol path at `state.source_file_line`.
4. Copy the range for the innermost symbol using
   `source_file_module.source_range_markdown`.

### File Detail

1. Reuse `_file_detail_source_target(...)` to map current rendered diff row to a
   repo-local path and new-file line.
2. Apply the same Source File symbol copy behavior to that path and line.
3. Keep the browser on File Detail.

## Errors

- Not on Source File or File Detail: `No source symbol to copy.`
- Current File Detail row has no new-file line: existing
  `No current new-file line in File Detail.`
- No symbol at current line: `No source symbol at current line.`
- Source read errors: surface existing source-file error messages.

## Boundaries

The command reuses the existing regex outline and source range Markdown. It does
not mutate source selection state and does not introduce any new persisted state.
