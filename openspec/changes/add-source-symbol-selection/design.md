# Design

## Command Shape

`source select symbol` works only on `BrowserPage.SOURCE_FILE`.

Aliases:

- `source select symbol`
- `select source symbol`
- `source symbol`

## Behavior

1. Load the current Source File content using the existing safe repo-local reader.
2. Parse the content with the existing regex-based `cr.source.outline` module.
3. Find the symbol path at `state.source_file_line`.
4. Pick the last symbol in the path, because it is the innermost class/function/method.
5. Set `state.source_selection_start` and `state.source_selection_end` to that
   symbol's `line` and `end_line`.
6. Show a status message containing the selected symbol label and range.
7. Redraw the current Source File page so the selection markers are visible.

## Errors

- If not on Source File: `Open a source file before selecting source symbol.`
- If the source file cannot be read: surface the existing content error.
- If no symbol contains the current line: `No source symbol at current line.`

## Boundaries

The outline module remains best-effort and parser-free. Browser command parsing
owns the command surface; browser execution owns state mutation; source-file
viewing continues to own read-only content loading and range markdown.
