## Design

The feature composes existing UI handoff pieces:

- `cr.ui.task_problems` owns selected task problem facts.
- `cr.ui.source_file` owns source snippet formatting.
- `cr.review.data` plus `cr.review.snippet` already produce compact same-file diff snippets.
- Browser Action Execution owns clipboard side effects.

Add `cr.ui.problem_context` as a pure Markdown composition module. It does not read files, inspect Git, mutate browser state, copy to clipboard, or render terminal pages. Browser Action Execution gathers the selected problem/source target, source content, optional same-file changed file, and optional diff snippet, then calls this module to produce text.

## Behavior

`copy problem context` works on:

- Task Problems Page: uses the selected visible problem.
- Source File Page: uses the current source path and target line.

The source snippet uses the active Source File Page radius when on Source File Page, otherwise the default source context radius. If the source file cannot be read, the command reports the source read error and does not copy partial context.

The diff section is included only when the problem/source file exists in the current Review Scope's visible changes. If no matching change exists, the copied Markdown includes a short `No diff in current review scope.` note instead of failing.

## Boundaries

This command is a targeted handoff, not a new diagnostics system. It should not alter Review Scope, task state, source navigation state, or workspace persistence.
