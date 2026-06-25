# Design

## Behavior

The existing `next problem` / `prev problem` command path will branch for `BrowserPage.FILE_DETAIL`.

For File Detail:

1. Identify the current changed file from `state.visible_changes[state.selected]`.
2. Filter current parsed task problems to that path while preserving their original global indices.
3. Move to the next or previous problem for that path relative to `state.problem_selected`.
4. Update `state.problem_selected` to the selected global problem index.
5. Try to scroll the current file detail to the problem line using existing rendered diff line mapping.
6. If the problem line is not visible in the rendered diff, keep File Detail open and show a message.

This keeps the page stable and avoids changing review scope or file selection.

## Boundaries

- Command parsing stays unchanged.
- File Detail behavior lives in `src/cr/ui/browser.py`, near other browser command actions.
- Rendered row mapping continues to use `src/cr/ui/file_detail_navigation.py`.
- Task problem facts continue to come from the existing task output parser.

## Validation

- Add File Detail executor tests for `next problem` selecting the next problem in the current file and scrolling to the visible diff row.
- Add a test for a same-file problem whose line is not visible in the current diff.
- Run focused tests, OpenSpec validation, and full test discovery.
