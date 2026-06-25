# Design: view-file-detail-source-symbol

## Command Shape

`view source symbol` is a narrow extension of the existing source bridge:

- `view source` opens Source File at the current File Detail new-file line.
- `view source symbol` does the same, then applies the same lightweight outline selection as `source select symbol`.

Aliases are intentionally minimal to keep command discovery simple.

## Behavior

1. In File Detail, resolve the current new-file line using the existing rendered-row mapping.
2. Open Source File with `BrowserNavigation.show_source_file(state, path, line)`.
3. Load the source file through the existing source-file boundary.
4. Parse the lightweight outline and find the innermost symbol at the target line.
5. If found, set `source_selection_start` and `source_selection_end` to that symbol range.
6. If not found, leave selection cleared and keep the Source File open at the target line.

## Boundaries

- Command parsing stays in `src/cr/ui/commands.py`.
- Execution stays in `src/cr/ui/browser.py`.
- Source facts continue to use `src/cr/source` helpers and the existing lightweight outline.
- Help and README document only the user-facing command.

## Validation

- Parser test for `view source symbol`.
- Executor test that File Detail opens Source File and selects the enclosing symbol.
- Executor test that a deleted-only/current old-file row stays on File Detail with the no-new-line message.
- Focused test command plus the full test suite if runtime permits.
