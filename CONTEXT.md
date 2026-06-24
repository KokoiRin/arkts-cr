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
facts; `cr.ui.browser` should own browse orchestration and terminal behavior,
while `cr.ui.navigation.BrowserNavigation` owns page transition rules,
in-session page history, and their small local state resets.
`cr.ui.workspace.ReviewWorkspace` owns active review scope state, changed-file
loading, filtering, progress markers, per-file review notes, selected-file
state, and browser workspace-state data interpretation.
`cr.ui.commands` owns browser command parsing: it translates typed commands,
key aliases, parameterized commands, numeric selections, and unknown input into
stable product actions without executing those actions, rendering output, or
mutating browser state.
`cr.ui.browser.BrowserCommandExecutor` owns browser action execution for parsed
commands: it mutates browser state and calls UI edge helpers, then returns loop
control (`needs_redraw` / `exit_code`) without reading raw input or saving
workspace state.
`cr.ui.file_actions` owns configured and platform fallback clipboard /
file-browser reveal helpers for browser file actions. It does not parse browser
commands or choose the selected review file.
`cr.ui.tasks` owns Task Panel runtime behavior: task command resolution,
command-source diagnostics, preset-format help, background process lifecycle,
output capture, stopping, rerun, foreground run, and completion history. It
does not render terminal panels or manage browser pages. `cr.ui.tasks` also
owns project-local task preset discovery from `.cr/tasks.json`; CLI arguments
and environment variables remain higher priority overrides.

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
- `Browser Navigation`: the internal module that moves between Scope Home,
  Commit Picker, Changed Files, File Detail, and Command Palette, including
  in-session back/forward page history, without loading Git data or rendering
  terminal output.
- `Review Workspace`: the internal module that owns the current Review Scope,
  changed files, filter/progress/note state, selected file, selected commit,
  previous scope, and persistence data mapping for `cr browse`.
- `Review Notes`: lightweight per-file notes inside the current Review
  Workspace, surfaced by `note TEXT` / `note` and persisted with browse state.
- `Browser Command Dispatch`: the internal module that maps command text and
  key aliases to stable browser actions. It parses intent but does not execute
  it.
- `Browser Action Execution`: the internal interface that executes parsed
  browser actions and returns loop control. It does not read prompt input or
  own browser session shutdown.
- `File Actions`: selected-file workbench operations such as `copy path`,
  `copy anchor`, and `reveal`. They act within the current Changed Files
  selection, support CLI/env command configuration, and do not create a new
  review hierarchy level.
- `Task Runtime`: the internal module behind Task Panel behavior. It owns
  process lifecycle and task history, while terminal layout and panel rendering
  stay with the browser frame.
- `Task Presets`: project-local default build/test/lint commands read from
  `.cr/tasks.json` by Task Runtime. Presets are defaults, not overrides for
  explicit CLI arguments or environment variables.
- `Task Diagnostics`: source explanations for build/test/lint command
  resolution, surfaced by `tasks` without starting a background task.
- `Task Preset Help`: a small help surface for `.cr/tasks.json`, surfaced by
  `tasks help` without starting a background task.
