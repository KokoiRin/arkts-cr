# cr Context

`cr` is a terminal-first review helper for local Git changes. The codebase is
organized around four module groups:

- `cr.vcs`: version-control adapters. This package owns Git process calls,
  diff scopes, file status, untracked-file handling, and repository paths.
- `cr.source`: source-file intelligence. This package owns lightweight
  language-outline parsing and purpose hints derived from paths and symbols.
- `cr.review`: review workflow, facts, and renderers. This package owns
  `cr review` execution, reusable changed-file facts, review data assembly,
  hunk rendering, changed-file trees, summaries, risk hints, and prompt
  handoff formatting.
- `cr.ui`: terminal interaction. This package owns terminal styling,
  clickable links, and the interactive browse session.

The root `cr` package should stay shallow: `cr.cli` parses commands and
delegates to these deeper modules. New behavior should usually land in one of
the four module groups before the CLI knows about it. In particular,
`cr.review.workflow.run_review` is the interface for the review command, while
`cr.review.changes` owns shared review-scope facts used by both `review` and
`diff`. The interactive browser also reuses `cr.review.changes` for changed-file
selection, sorting, code-file detection, hunk rendering, and modified-symbol
facts; `cr.ui.browser` should only own interaction state and terminal behavior.

Product navigation terms:

- `Review Scope`: the top-level changed set being reviewed, such as worktree,
  staged, all local changes, base ref, explicit range, or a selected commit.
- `Changed Files`: the file tree/list inside one Review Scope.
- `File Detail`: the per-file diff, symbol, purpose, and editor-handoff layer
  inside one Changed Files set.
- `Command Palette`: a cross-layer action surface, not a review hierarchy level.
- `Task Panel`: a screen-rendering region for background tasks, not a review
  hierarchy level.
- `Browser Frame`: the raw-key terminal frame that owns context/status, main
  content, task panel, and prompt regions.
