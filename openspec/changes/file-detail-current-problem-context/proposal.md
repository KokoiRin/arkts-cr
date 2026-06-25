# File Detail current problem context

## Why

File Detail is now current-row aware for `copy problem`, `save problem`, and problem diff handoff. `copy problem context` still packages only source and diff while on File Detail, even when the current diff row exactly matches a build/test/lint problem. That leaves users one step short of the main handoff shape: problem + source + task output + diff.

## What changes

- In File Detail, `copy problem context` includes the matching task problem and nearby task output when the current rendered new-file line has a parsed problem.
- In File Detail, `save problem context [PATH]` saves the same enriched context.
- If the current row has no matching task problem, File Detail keeps the existing source + diff context behavior.
- File Detail never falls back to the globally selected task problem for context enrichment.

## Non-goals

- No stricter requirement that File Detail context must have a task problem.
- No diagnostics persistence.
- No parser, language-service, quick-fix, source editing, or cross-file dependency expansion.
