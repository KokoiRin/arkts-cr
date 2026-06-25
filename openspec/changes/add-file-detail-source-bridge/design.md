# Design

## Command Shape

`view source` works on File Detail.

Aliases:

- `view source`
- `source view`
- `view current source`

## Behavior

1. Confirm the browser is on `BrowserPage.FILE_DETAIL`.
2. Read the selected changed file from `state.visible_changes`.
3. Reuse `_cached_file_lines(...)` and
   `file_detail_navigation.current_new_line(...)` to map `state.file_scroll` to
   a new-file source line.
4. Call `BrowserNavigation.show_source_file(state, change.path, line)`.
5. Leave File Detail state available in the back stack so `b` returns to the
   same file and scroll.

## Errors

- Outside File Detail: `Open a file detail to view source.`
- No visible changed file: `No changed file to view source.`
- Current rendered row has no new-file line: `No current new-file line in File Detail.`

## Boundaries

The command belongs in browser command parsing/execution because it is a page
transition. Source reading remains owned by `cr.ui.source_file`; line mapping
remains owned by `cr.ui.file_detail_navigation`.
