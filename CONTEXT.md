# cr Context

`cr` is a terminal-first review helper for local Git changes. The codebase is
organized around four module groups:

- `cr.vcs`: version-control adapters. This package owns Git process calls,
  diff scopes, file status, untracked-file handling, and repository paths.
- `cr.source`: source-file intelligence. This package owns lightweight
  language-outline parsing and purpose hints derived from paths and symbols.
- `cr.review`: review facts and renderers. This package owns review data
  assembly, hunk rendering, changed-file trees, summaries, risk hints, and
  prompt handoff formatting.
- `cr.ui`: terminal interaction. This package owns terminal styling,
  clickable links, and the interactive browse session.

The root `cr` package should stay shallow: `cr.cli` parses commands and
delegates to these deeper modules. New behavior should usually land in one of
the four module groups before the CLI knows about it.

