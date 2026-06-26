# OpenSpec Index

Canonical specs are split by product behavior domain. Keep new user-visible requirements in the closest domain spec instead of rebuilding a monolith.

| Spec | Requirements | Purpose |
| --- | ---: | --- |
| `cli-review-workflows` | 5 | Non-interactive `cr diff`, `cr outline`, and `cr review` behavior. |
| `review-scope-workspace` | 26 | Choosing review scopes, preserving workspace state, progress markers, and commit selection. |
| `changed-files-and-actions` | 32 | Changed-file list behavior, source filters, selected-file actions, and editor/file handoff. |
| `file-detail-reading` | 21 | Per-file diff reading, hunk navigation, line/change actions, and File Detail problem handoff. |
| `source-reading-symbols` | 41 | Read-only source preview, source selection, source context, and lightweight symbol recognition. |
| `task-panel-output` | 43 | Background build/test/lint task runtime, Task Panel rendering, Task Output reading, and output handoff. |
| `task-problems` | 38 | Problems extracted from task output, problem navigation, filtering, grouping, and problem handoff. |
| `prompt-context-handoff` | 4 | Prompt, diff, source, problem, task-output, and review-note handoff packages. |
| `review-notes` | 11 | Per-file review notes, note summaries, note filtering, copying, saving, and persistence. |
| `command-palette-help` | 19 | In-session command discovery, executable command palette, page help, and command catalog behavior. |
| `tui-frame-navigation` | 18 | Terminal frame regions, raw-key input, page model, breadcrumbs, navigation history, and redraw rules. |
| `workbench-architecture` | 13 | Module ownership and locality contracts that keep product behavior maintainable. |
