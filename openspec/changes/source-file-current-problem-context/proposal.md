# Source File current problem context

## Why

Source File can show a `problem:` header when the current source line exactly matches the selected task problem. However, `copy problem context` and `save problem context` still package only source and diff from Source File. Users reading the failing source line have to return to Task Problems or Task Output to include the diagnostic and nearby log lines.

## What changes

- In Source File, `copy problem context` includes the current matching task problem and nearby task output when the current source line exactly matches the selected parsed problem.
- In Source File, `save problem context [PATH]` saves the same enriched context.
- Source selection still controls the source excerpt when a range or symbol is selected.
- If the current source line has no exact matching problem, Source File keeps the existing source + diff context behavior and does not fall back to a stale selected problem.

## Non-goals

- No diagnostics persistence.
- No automatic source selection or symbol expansion.
- No parser, language-service, quick-fix, source editing, or cross-file dependency expansion.
