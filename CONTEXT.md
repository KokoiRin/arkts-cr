# cr Context

`cr` is a terminal-first review helper for local Git changes. The codebase is
organized around four module groups:

- `cr.vcs`: version-control adapters. This package owns Git process calls,
  diff scopes, file status, local change source facts, untracked-file handling,
  and repository paths.
- `cr.source`: source-file intelligence. This package owns lightweight
  language-outline parsing and purpose hints derived from paths and symbols.
- `cr.review`: review workflow, facts, and renderers. This package owns
  `cr review` execution, reusable changed-file facts, review data assembly,
  hunk rendering, changed-file trees, summaries, risk hints, prompt handoff
  formatting, and compact selected-file review snippets.
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
help lines, scope breadcrumbs/context, Scope Home entries and overview counts,
Changed Files tree rows including local change source badges and summaries,
Commit Picker rows and change summaries, empty states, File Detail lines, Task
Output Page lines, and page scroll window calculations. It does not read raw
input, draw the Browser Frame, run commands, switch review scopes, persist
workspace state, or execute file actions.
`cr.ui.commit_picker` owns Commit Picker rules: commit search text, loaded
commit filtering, and filtered selection helpers. It does not render terminal
rows, parse commands, load commits from Git, draw the Browser Frame, or persist
workspace state.
`cr.ui.workspace.ReviewWorkspace` owns active review scope state, changed-file
loading/reloading, selected-path restoration after reload, path/source
filtering, progress markers, per-file review notes, selected-file state, and
browser workspace-state data interpretation.
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
`cr.ui.review_notes` owns Review Notes summary/search/copy behavior: ordered
note summary lines, path/text filtering, empty-state text, and copy status
messages. It does not edit notes, persist workspace state, parse commands, or
place Browser Frame feedback.
`cr.ui.file_detail_navigation` owns rendered File Detail navigation: detecting
hunk header rows, choosing next/previous target scroll positions, resolving the
active hunk's new-file line, extracting the active rendered hunk block, finding
rendered text, and returning navigation status messages. It does not render
file content, parse commands, mutate browser state, or read Git diff data.
`cr.ui.text_search` owns generic plain-text search over already-rendered
terminal lines, including ANSI-style stripping and wraparound match selection.
It does not know browser pages, Git diff structure, task runtime, or scroll
state owners.
`cr.ui.browser.BrowserCommandExecutor` owns browser action execution for parsed
commands: it mutates browser state and calls UI edge helpers, then returns loop
control (`needs_redraw` / `exit_code`) without reading raw input or saving
workspace state.
`cr.ui.selected_file_actions` owns selected-file action workflow: open selected
file, open/copy selected hunk, copy path/anchor/diff, save diff, reveal,
stage/unstage selected files, set/clear selected-file note, prompt handoff
selection, and copy/save prompt handoff messages. It does not
summarize/search/copy all review notes, parse commands, place status messages
in the Browser Frame, or own platform subprocess details.
`cr.ui.file_actions` owns configured and platform fallback open/copy/reveal
helpers, subprocess launches, and source diagnostics for browser file actions.
It does not parse browser commands or choose the selected review file.
`cr.ui.handoff` owns UI-side handoff file output: default save paths,
repo-relative and absolute path resolution, UTF-8 writes, parent directory
creation, and write-error messages. It does not render prompt/snippet Markdown
or choose browser files.
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
`cr.ui.task_problems` owns lightweight file-location extraction from current
task output. It recognizes repo-local `path:line[:column]` anchors and returns
Task Problem facts and handoff text; it does not manage task lifecycle, render
pages, open editors, copy to clipboards, parse severity, or persist diagnostics.
`cr.ui.source_file` owns read-only repo-local source-file preview facts:
UTF-8 file reads, target-line clamping, and visible-window rows. It does not
render terminal pages, edit files, parse syntax, open editors, or persist
source-view state.

Product navigation terms:

- `Review Scope`: the top-level changed set being reviewed, such as worktree,
  staged, all local changes, base ref, explicit range, or a selected commit.
- `Changed Files`: the file tree/list inside one Review Scope.
- `File Detail`: the per-file diff, symbol, purpose, and editor-handoff layer
  inside one Changed Files set.
- `Command Palette`: a cross-layer action surface, not a review hierarchy level.
- `Task Panel`: a screen-rendering region for background tasks, not a review
  hierarchy level.
- `Task Output Page`: a browser page for reading the current task's captured
  output with its own scroll and find state. It is an Output Panel-style detail
  view for Task Panel data, not a new review hierarchy level and not task
  history.
- `Task Problems Page`: a browser page for current task output anchors that
  look like repo-local `path:line[:column]` locations. It is a lightweight
  Problems panel, not a persisted diagnostics model and not task history.
- `Source File Page`: a cross-layer browser page for read-only repo-local
  source previews, usually opened from Task Problems. It is not File Detail,
  does not require the file to be changed in the current Review Scope, and does
  not edit files. It has its own `source_find_text` for single-file text search.
- `Browser Frame`: the raw-key terminal frame that owns context/status, main
  content, task panel, and prompt regions. Internally, `cr.ui.frame` owns the
  screen-layer layout and Task Panel presentation helpers.
- `Browser Input`: the internal module that reads browser terminal input and
  returns stable command/query/sentinel tokens. It owns raw-key detection,
  escape-sequence mapping, idle tick, EOF, interrupt, and temporary line query
  reading, while `browser.py` decides how those tokens affect product state.
- `Page Content`: the internal module that renders product-page main content
  for Scope Home, Commit Picker, Changed Files, empty states, File Detail, and
  Task Output Page, Task Problems Page, and Source File Page. It owns page text
  and scroll-window rendering rules, while Browser Frame owns screen placement.
- `Scope Home Counts`: temporary overview counts shown on Scope Home for
  Worktree, Staged, All local changes, and Recent commits. Browser
  orchestration samples these counts when Scope Home opens or refreshes; Page
  Content renders them; workspace persistence does not store them.
- `Commit Picker Change Summary`: per-commit file count and added/deleted line
  totals shown in Recent commits rows. `cr.vcs.git` owns the facts; Page
  Content owns row display; selecting a commit still enters the same
  `commit <sha>` Review Scope.
- `Commit Picker Filter`: temporary filtering inside Recent commits, matching
  loaded commits by hash, date, subject, or displayed change summary. It is
  browser-local UI state, not Review Workspace state, and `c` clears it without
  touching the Changed Files path filter. Internally, `cr.ui.commit_picker`
  owns the matching and filtered selection rules while Page Content owns row
  rendering.
- `Change Source Badges`: lightweight local Git source labels shown in Changed
  Files rows, such as `staged`, `unstaged`, and `mixed`. `cr.vcs.git` owns the
  facts; `Page Content` owns row display.
- `Change Source Filter`: a Changed Files view filter controlled by
  `source staged` / `source unstaged` / `source mixed` / `source all`. It is
  owned by Review Workspace and composes with path filters and remaining-only
  review progress.
- `Change Source Summary`: a Changed Files metadata line that counts visible
  `staged`, `unstaged`, and `mixed` local source facts. It is derived by Page
  Content from the currently rendered changes and is not persisted workspace
  state.
- `Contextual Action Bar`: a one-line raw-key frame hint showing the most useful
  actions for the current page. Page Content owns the per-page action text;
  Browser Frame owns placement constraints and line fitting; the action bar is
  not command state, workspace state, or persisted data.
- `Browser Navigation`: the internal module that moves between Scope Home,
  Commit Picker, Changed Files, File Detail, Command Palette, Task Output Page,
  Task Problems Page, and Source File Page, including in-session back/forward
  page history, without loading Git data or rendering terminal output.
- `Review Workspace`: the internal module that owns the current Review Scope,
  changed files, path/source filter state, progress/note state, selected file,
  selected commit, previous scope, and persistence data mapping for `cr browse`.
- `Workspace Persistence`: the internal module that owns `.git/cr/browse-state.json`
  path construction, version validation, tolerant JSON read/write, and default
  workspace save/restore eligibility.
- `Review Notes`: lightweight per-file notes inside the current Review
  Workspace, surfaced by `note TEXT` / `note` / `notes` / `notes QUERY` /
  `copy notes` / `copy notes QUERY` and persisted with browse state. Internally,
  `cr.ui.review_notes` owns summary, filtering, and copy behavior while
  `ReviewWorkspace` owns stored note data.
- `Review Progress`: lightweight per-file seen/todo state inside the current
  Review Workspace, surfaced by `m` / `seen` / `done`, `done next` /
  `seen next`, `todo` / `unseen` / `unmark`, `remaining`, and `allfiles`.
  `ReviewWorkspace` owns stored `seen_paths`, remaining-only filtering, and
  selected-file progress operations including mark, unmark, and
  mark-and-advance selection rules. Browser Action Execution only coordinates the
  page-aware part of mark-and-advance, such as reopening File Detail and placing
  status feedback.
- `Prompt Handoff`: Markdown review context copied or saved from the current
  browser Review Scope or selected file through `copy prompt` /
  `copy prompt file` / `save prompt` / `save prompt file`. It reuses
  `cr.review` prompt rendering, including supplied review notes, instead of
  defining browser-specific prompt text.
- `File Diff Snippet`: compact Markdown review context for one selected file,
  copied through `copy diff` or saved through `save diff`. It reuses structured
  review data and `cr.review.snippet` rendering, includes selected-file hunks
  and metadata, and is not the full AI prompt handoff format.
- `File Detail Hunk Navigation`: within File Detail, `next hunk` / `]` and
  `prev hunk` / `[` move the file scroll between rendered diff hunk headers,
  while `open hunk` opens the active hunk's new-file line in the editor and
  `copy hunk` copies the active rendered hunk block as compact review context.
  `find TEXT` searches the current rendered File Detail text, and `next match`
  / `prev match` repeat the last non-empty File Detail query. `open line` and
  `copy line` act on the current rendered File Detail row when that row has a
  new-file line number. `next change` and `prev change` jump between actual
  added/deleted rows inside the rendered File Detail, and `copy change` copies
  the current actual changed row as a compact single-row review snippet.
  `note change TEXT` appends the current actual changed row position to the
  selected file's existing review note. This is local navigation/action inside
  the current selected file, not a new product hierarchy layer or separate
  comments model.
- `Task Output Find`: within Task Output Page, `find TEXT` searches current
  captured task output, while `next match` / `prev match` repeat the last
  non-empty task-output query with wraparound. It uses separate `task_find_text`
  state from File Detail's `file_find_text` and does not search TaskRecord
  history or parse diagnostics.
- `Task Problems`: within Task Problems Page, `problems` / `task problems`
  lists repo-local file anchors extracted from current task output. Enter opens
  the selected problem through File Actions, `view problem` opens the selected
  problem in Source File Page, while `copy problem` and `copy problems` hand off
  selected/all current problems through the existing clipboard action. This is
  intentionally lighter than a full diagnostics parser: no severity, no error
  codes, no history, and no workspace persistence.
- `Source File Find`: within Source File Page, `find TEXT` searches the current
  repo-local source preview, while `next match` / `prev match` repeat the last
  non-empty source query with wraparound. It is source-page-local state, not
  File Detail find, Task Output find, cross-file search, syntax search, or
  persisted workspace state.
- `Browser Command Dispatch`: the internal module that maps command text and
  key aliases to stable browser actions. It parses intent but does not execute
  it.
- `Command Catalog`: the internal module that owns grouped command help,
  executable Command Palette entries, filtering/ranking, and command surface
  row rendering. It does not parse command text or execute actions.
- `Review Notes Module`: the internal module that owns ordered note summary
  lines, path/text filtering, empty-state text, and note-copy status messages.
  It receives changed-file and note data explicitly, and does not mutate
  browser state.
- `Browser Action Execution`: the internal interface that executes parsed
  browser actions and returns loop control. It does not read prompt input or
  own browser session shutdown.
- `Selected File Actions`: the internal module that owns workflows acting on
  the current Changed Files selection, including open, open/copy hunk,
  open/copy line, copy change, note current change, copy path, copy anchor,
  copy/save diff snippet, reveal, stage/unstage, selected-file notes, and
  selected/scope prompt handoff selection. All-note summary/search/copy behavior
  stays in Review Notes Module; platform subprocess details stay in File
  Actions; Git index mutations stay in `cr.vcs.git`.
- `File Actions`: selected-file workbench operations such as `open`,
  `copy path`, `copy anchor`, `copy diff`, `copy hunk`, `save diff`,
  `copy prompt file`, `save prompt file`, and `reveal`. They act within the
  current Changed Files selection, support CLI/env command configuration where
  applicable, and do not create a new review hierarchy level.
- `Index Actions`: selected-file workbench operations such as `stage` and
  `unstage`. They mutate the local Git index only for mutable local review
  scopes, then refresh Changed Files without creating a new product layer.
- `File Action Diagnostics`: source explanations for `open`, `copy`, and
  `reveal`, surfaced by `file actions` and failure messages without executing
  diagnostics commands.
- `Task Runtime`: the internal module behind Task Panel behavior. It owns
  process lifecycle, task history, and current task output handoff text, while
  terminal layout and panel presentation stay with Browser Frame. Clipboard and
  file writes for task output remain UI edge behavior outside Task Runtime.
- `Task Presets`: project-local default build/test/lint commands read from
  `.cr/tasks.json` by Task Runtime. Presets are defaults, not overrides for
  explicit CLI arguments or environment variables.
- `Task Diagnostics`: source explanations for build/test/lint command
  resolution, surfaced by `tasks` without starting a background task.
- `Task Preset Help`: a small help surface for `.cr/tasks.json`, surfaced by
  `tasks help` without starting a background task.
