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
facts; `cr.ui.browser` should own browse orchestration, prompt-input
interpretation, Browser Frame composition, and session startup/shutdown, while
`cr.ui.navigation.BrowserNavigation` owns page transition rules, in-session page
history, and their small local state resets.
`cr.ui.input` owns browser terminal input protocol: raw-key availability,
browse command reads, temporary filter/command query reads, raw escape-sequence
mapping, idle tick/EOF/interrupt sentinels, and terminal raw-mode restoration.
It does not parse browser commands, mutate browser state, save workspace state,
or draw the Browser Frame.
`cr.ui.page_content` owns browser page main-content rendering: prompt labels,
help lines, scope breadcrumbs/context, Scope Home entries, Changed Files tree
rows, Commit Picker rows, empty states, File Detail lines, and page scroll
window calculations. It does not read raw input, draw the Browser Frame, run
commands, switch review scopes, persist workspace state, or execute file
actions.
`cr.ui.workspace.ReviewWorkspace` owns active review scope state, changed-file
loading, filtering, progress markers, per-file review notes, selected-file
state, and browser workspace-state data interpretation.
`cr.ui.workspace_persistence` owns browser workspace persistence file I/O:
`.git/cr/browse-state.json` path construction, schema version wrapping and
validation, tolerant JSON read/write, and default-session save/restore
eligibility.
`cr.ui.commands` owns browser command parsing: it translates typed commands,
key aliases, parameterized commands, numeric selections, and unknown input into
stable product actions without executing those actions, rendering output, or
mutating browser state.
`cr.ui.command_catalog` owns the browser command surface: grouped command help,
executable Command Palette entries, command filtering/ranking, and command
surface row rendering. It does not parse typed commands or execute actions.
`cr.ui.browser.BrowserCommandExecutor` owns browser action execution for parsed
commands: it mutates browser state and calls UI edge helpers, then returns loop
control (`needs_redraw` / `exit_code`) without reading raw input or saving
workspace state.
`cr.ui.selected_file_actions` owns selected-file action workflow: open selected
file, copy path/anchor, reveal, set/clear selected-file note, prompt handoff
selection, and copy/save prompt handoff messages. It does not parse commands,
place status messages in the Browser Frame, or own platform subprocess details.
`cr.ui.file_actions` owns configured and platform fallback open/copy/reveal
helpers, subprocess launches, and source diagnostics for browser file actions.
It does not parse browser commands or choose the selected review file.
`cr.ui.handoff` owns UI-side handoff file output: default save paths,
repo-relative and absolute path resolution, UTF-8 writes, parent directory
creation, and write-error messages. It does not render prompt Markdown or
choose browser files.
`cr.ui.frame` owns Browser Frame screen-layer behavior: terminal height and line
fitting, content/task/prompt region layout, Task Panel line presentation, and
Task Panel-only refresh output. It does not generate page-specific review
content, run task processes, parse commands, or own workspace state.
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
  content, task panel, and prompt regions. Internally, `cr.ui.frame` owns the
  screen-layer layout and Task Panel presentation helpers.
- `Browser Input`: the internal module that reads browser terminal input and
  returns stable command/query/sentinel tokens. It owns raw-key detection,
  escape-sequence mapping, idle tick, EOF, interrupt, and temporary line query
  reading, while `browser.py` decides how those tokens affect product state.
- `Page Content`: the internal module that renders product-page main content
  for Scope Home, Commit Picker, Changed Files, empty states, and File Detail.
  It owns page text and scroll-window rendering rules, while Browser Frame owns
  screen placement.
- `Browser Navigation`: the internal module that moves between Scope Home,
  Commit Picker, Changed Files, File Detail, and Command Palette, including
  in-session back/forward page history, without loading Git data or rendering
  terminal output.
- `Review Workspace`: the internal module that owns the current Review Scope,
  changed files, filter/progress/note state, selected file, selected commit,
  previous scope, and persistence data mapping for `cr browse`.
- `Workspace Persistence`: the internal module that owns `.git/cr/browse-state.json`
  path construction, version validation, tolerant JSON read/write, and default
  workspace save/restore eligibility.
- `Review Notes`: lightweight per-file notes inside the current Review
  Workspace, surfaced by `note TEXT` / `note` / `notes` / `notes QUERY` /
  `copy notes` / `copy notes QUERY` and persisted with browse state.
- `Prompt Handoff`: Markdown review context copied or saved from the current
  browser Review Scope or selected file through `copy prompt` /
  `copy prompt file` / `save prompt` / `save prompt file`. It reuses
  `cr.review` prompt rendering, including supplied review notes, instead of
  defining browser-specific prompt text.
- `Browser Command Dispatch`: the internal module that maps command text and
  key aliases to stable browser actions. It parses intent but does not execute
  it.
- `Command Catalog`: the internal module that owns grouped command help,
  executable Command Palette entries, filtering/ranking, and command surface
  row rendering. It does not parse command text or execute actions.
- `Browser Action Execution`: the internal interface that executes parsed
  browser actions and returns loop control. It does not read prompt input or
  own browser session shutdown.
- `Selected File Actions`: the internal module that owns workflows acting on
  the current Changed Files selection, including open, copy path, copy anchor,
  reveal, selected-file notes, and selected/scope prompt handoff selection.
  Platform subprocess details stay in File Actions.
- `File Actions`: selected-file workbench operations such as `open`,
  `copy path`, `copy anchor`, `copy prompt file`, `save prompt file`, and
  `reveal`. They act within the current Changed Files selection, support
  CLI/env command configuration where applicable, and do not create a new
  review hierarchy level.
- `File Action Diagnostics`: source explanations for `open`, `copy`, and
  `reveal`, surfaced by `file actions` and failure messages without executing
  diagnostics commands.
- `Task Runtime`: the internal module behind Task Panel behavior. It owns
  process lifecycle and task history, while terminal layout and panel
  presentation stay with Browser Frame.
- `Task Presets`: project-local default build/test/lint commands read from
  `.cr/tasks.json` by Task Runtime. Presets are defaults, not overrides for
  explicit CLI arguments or environment variables.
- `Task Diagnostics`: source explanations for build/test/lint command
  resolution, surfaced by `tasks` without starting a background task.
- `Task Preset Help`: a small help surface for `.cr/tasks.json`, surfaced by
  `tasks help` without starting a background task.
