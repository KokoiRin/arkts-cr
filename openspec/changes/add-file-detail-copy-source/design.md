# Design

## Command Shape

`copy source` keeps the existing command name.

Page behavior:

- Source File: unchanged; copy selected range or target-line context.
- File Detail: copy source context around the current rendered new-file line.
- Other pages: keep the existing `No source file to copy.` message.

## File Detail Target Rule

1. Confirm the browser is on `BrowserPage.FILE_DETAIL`.
2. Read the selected changed file from `state.visible_changes`.
3. Reuse `_cached_file_lines(...)` and
   `file_detail_navigation.current_new_line(...)` to map `state.file_scroll` to
   a new-file line.
4. Load that repo-local source file with `source_file_module.load_source_file_content`.
5. Render context Markdown with `source_file_module.source_context_markdown`.
6. Include the same best-effort symbol metadata used by Source File.
7. Copy through the existing `file_actions.copy_text` boundary.

## Errors

- Deleted-only/current row without a new-file line:
  `No current new-file line in File Detail.`
- No visible changed file: `No changed file to copy source.`
- Source read errors: surface existing source-file errors.

## Boundaries

Line mapping stays in `cr.ui.file_detail_navigation`; source reads and Markdown
formatting stay in `cr.ui.source_file`; browser execution only chooses the
page-specific target and invokes the copy boundary.
