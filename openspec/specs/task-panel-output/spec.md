# Task Panel and Task Output Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Background build/test/lint task runtime, Task Panel rendering, Task Output reading, and output handoff.

## Requirements
### Requirement: 任务输出 handoff 不改变任务运行时
系统 MUST 将 task output handoff 作为命令副作用处理，不改变 task lifecycle、task history 或 workspace persistence。

#### Scenario: Command parsing remains explicit
- **WHEN** 用户输入 `copy task` 或 `save task`
- **THEN** command parser SHALL 返回专用 task output handoff action

#### Scenario: Workspace persistence unchanged
- **WHEN** 浏览器保存 workspace state
- **THEN** persisted data SHALL NOT include task output handoff content

### Requirement: Task Output handoff uses selected problem

Task Output problem actions SHALL target the current visible parsed problem
selection.

#### Scenario: View selected Task Output problem source

- **GIVEN** Task Output has multiple visible parsed problems and the second
  problem is selected
- **WHEN** the user runs `view problem`
- **THEN** Source File Page SHALL open at the second problem's source location.

#### Scenario: Copy selected Task Output problem context

- **GIVEN** Task Output has multiple visible parsed problems and the second
  problem is selected
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL describe the second problem.

### Requirement: Build panel isolated refresh
`cr browse` SHALL update build output without scrolling or clearing the main browser screen.

#### Scenario: Background build output changes
- **WHEN** the build process emits new output while the user is idle
- **THEN** the browser SHALL update only the build panel rows
- **AND** the browser SHALL NOT clear the full screen
- **AND** the browser SHALL preserve the cursor position used for command input

#### Scenario: Background build output unchanged
- **WHEN** the build panel contents have not changed since the previous render
- **THEN** the browser SHALL NOT write a duplicate panel frame

### Requirement: Stop running build
`cr browse` SHALL allow users to stop a running background build from the interactive browser.

#### Scenario: Stop a running build
- **WHEN** a build is running and the user enters a stop command
- **THEN** the browser SHALL request termination of the build process
- **AND** the build panel SHALL show a stopping or stopped state
- **AND** the browser SHALL remain in the current review view

#### Scenario: Stop when no build is running
- **WHEN** no build is running and the user enters a stop command
- **THEN** the browser SHALL keep the session open
- **AND** the build panel or command feedback SHALL explain that no build is running

### Requirement: Rerun build
`cr browse` SHALL allow users to rerun the configured build command after a prior build is not running.

#### Scenario: Rerun after build completes
- **WHEN** a build has completed or stopped and the user enters a rerun command
- **THEN** the browser SHALL start the configured build command again
- **AND** the build panel SHALL show the new build output

#### Scenario: Rerun while build is running
- **WHEN** a build is currently running and the user enters a rerun command
- **THEN** the browser SHALL NOT start a second build process
- **AND** the build panel SHALL tell the user to stop the current build first

### Requirement: Build lifecycle status
The build panel SHALL distinguish user-stopped builds from failed builds.

#### Scenario: User-stopped build exits
- **WHEN** the user has requested stop and the build process exits
- **THEN** the build panel SHALL show `stopped`
- **AND** the build log SHALL include `Build stopped.`

#### Scenario: Build exits without stop request
- **WHEN** the build process exits without a user stop request
- **THEN** the build panel SHALL continue to show `succeeded` for exit code 0
- **AND** the build panel SHALL continue to show `failed (<code>)` for non-zero exit codes

### Requirement: Background build process group
`cr browse` SHALL run each interactive background build in an isolated process group when the platform supports it.

#### Scenario: Start background build
- **WHEN** the browser starts a background build
- **THEN** the build process SHALL be started in an isolated process group
- **AND** the build state SHALL remember the process group id

### Requirement: Stop build process group
`cr browse` SHALL stop the whole background build process group when the user cancels a running build.

#### Scenario: Stop build with child processes
- **WHEN** a background build has spawned child processes
- **AND** the user enters `stop` or `cancel`
- **THEN** the browser SHALL request termination of the build process group
- **AND** child processes in that group SHALL not continue running after the build is stopped
- **AND** the browser SHALL remain in the current review view

#### Scenario: Process group termination fails
- **WHEN** the user stops a running build
- **AND** terminating the build process group fails
- **THEN** the browser SHALL try to terminate the parent build process
- **AND** the build panel SHALL show a readable stop failure message

### Requirement: Existing build states remain stable
Process group cleanup SHALL preserve the existing build panel lifecycle states.

#### Scenario: User-stopped build exits
- **WHEN** the user has requested stop and the build process exits
- **THEN** the build panel SHALL continue to show `stopped`
- **AND** the build log SHALL continue to include `Build stopped.`

### Requirement: Escalate unresponsive build stop
`cr browse` SHALL force-kill a stopped background build that remains running past the grace period.

#### Scenario: Build ignores graceful stop
- **WHEN** the user has requested a build stop
- **AND** the build process group is still running after the grace period
- **THEN** the browser SHALL send a force-kill signal to the build process group
- **AND** the build log SHALL show that stop was escalated

#### Scenario: No process group is available
- **WHEN** the user has requested a build stop
- **AND** no build process group id is available
- **AND** the build is still running after the grace period
- **THEN** the browser SHALL force-kill the parent build process
- **AND** the browser SHALL NOT crash

### Requirement: Task panel records completed build tasks
`cr browse` SHALL keep a compact in-session history of completed background build tasks.

#### Scenario: Build completes
- **WHEN** a background build reaches a terminal state
- **THEN** the browser SHALL append one task history record
- **AND** the record SHALL include the task kind, command, status, and return code when available

#### Scenario: Build is polled repeatedly after completion
- **GIVEN** a completed build has already been recorded
- **WHEN** the browser polls again
- **THEN** it SHALL NOT append a duplicate history record for the same build

### Requirement: Task panel renders recent task history
`cr browse` SHALL show recent task results in the bottom task panel.

#### Scenario: Render build panel with history
- **GIVEN** one or more task history records exist
- **WHEN** the build panel is rendered
- **THEN** it SHALL show a compact recent-task summary
- **AND** it SHALL still show the current build status and latest log lines

#### Scenario: Rerun build after completion
- **GIVEN** a build has completed and been recorded
- **WHEN** the user starts another build
- **THEN** the build panel SHALL show the new current build
- **AND** it SHALL retain the previous build in recent task history for the session

### Requirement: Task history stays session-local
Task history SHALL NOT be persisted to browser workspace state.

#### Scenario: Save browser workspace
- **WHEN** browser workspace state is saved
- **THEN** task history SHALL NOT be written to `.git/cr/browse-state.json`

### Requirement: Browser runs test and lint tasks
`cr browse` SHALL support configured test and lint commands through the same background task panel used for build tasks.

#### Scenario: Start test task
- **GIVEN** a test command is configured
- **WHEN** the user enters `test` or `tests`
- **THEN** the browser SHALL start that command as the current background task
- **AND** the task panel SHALL identify it as a test task

#### Scenario: Start lint task
- **GIVEN** a lint command is configured
- **WHEN** the user enters `lint`
- **THEN** the browser SHALL start that command as the current background task
- **AND** the task panel SHALL identify it as a lint task

#### Scenario: Missing task command
- **GIVEN** no command is configured for the requested task kind
- **WHEN** the user starts that task
- **THEN** the task panel SHALL show a readable configuration message
- **AND** it SHALL NOT start a guessed command

### Requirement: Current task controls are task-kind aware
The browser SHALL apply stop and rerun controls to the current or most recent task kind.

#### Scenario: Stop current task
- **GIVEN** a build, test, or lint task is running
- **WHEN** the user enters `stop` or `cancel`
- **THEN** the browser SHALL stop the running task process group
- **AND** the panel SHALL describe the stopped task kind

#### Scenario: Rerun recent task
- **GIVEN** a test or lint task was the most recently started task
- **WHEN** the user enters `rerun`
- **THEN** the browser SHALL run the same task kind again

### Requirement: Task runtime reads project task presets
The system SHALL read project-local task presets from `.cr/tasks.json` at the repository root.

#### Scenario: Resolve task command from preset
- **WHEN** `.cr/tasks.json` contains a string command for `build`, `test`, or `lint`
- **THEN** the task runtime SHALL use that command when no CLI argument or environment variable overrides the same task kind

#### Scenario: Ignore invalid preset file
- **WHEN** `.cr/tasks.json` is missing, invalid JSON, not a JSON object, or contains a non-string value for a task kind
- **THEN** the task runtime SHALL ignore the invalid preset data and continue resolving commands from the remaining existing sources

### Requirement: Task command precedence remains explicit
The system SHALL resolve task commands using the precedence CLI argument, environment variable, project preset, DouyinHarmony build default, missing-command fallback.

#### Scenario: CLI argument overrides preset
- **WHEN** a task command is provided by CLI argument and `.cr/tasks.json` also contains that task kind
- **THEN** the CLI argument SHALL be used

#### Scenario: Environment variable overrides preset
- **WHEN** a task command is provided by environment variable and `.cr/tasks.json` also contains that task kind
- **THEN** the environment variable SHALL be used

#### Scenario: DouyinHarmony default remains build fallback
- **WHEN** the task kind is `build`, no CLI argument, environment variable, or project preset is present, and the repository is DouyinHarmony with `remote`
- **THEN** the existing DouyinHarmony build command SHALL be used

### Requirement: Browser shows task command diagnostics
The browser SHALL provide a `tasks` command that reports command sources for build, test, and lint.

#### Scenario: Show task sources
- **WHEN** the user runs `tasks`
- **THEN** the browser SHALL show source diagnostics for `build`, `test`, and `lint`
- **AND** SHALL NOT start or stop any task process

### Requirement: Task runtime explains command precedence
Task Runtime SHALL explain the winning task command source using the existing precedence CLI argument, environment variable, project preset, DouyinHarmony build default, missing.

#### Scenario: CLI, env, preset, default, and missing sources
- **WHEN** different task kinds are configured from different command sources
- **THEN** diagnostics SHALL identify the winning source for each task kind

### Requirement: Preset parsing diagnostics are non-fatal
Task Runtime SHALL report malformed `.cr/tasks.json` in diagnostics while preserving tolerant command resolution.

#### Scenario: Invalid preset file
- **WHEN** `.cr/tasks.json` is malformed
- **THEN** diagnostics SHALL include a preset warning
- **AND** command resolution SHALL continue to use other available sources

### Requirement: Browser opens current task output page

`cr browse` SHALL provide a page that displays the current task output inside the browser.

#### Scenario: Open Task Output page

- **WHEN** the user runs `task output` or `output`
- **THEN** the browser SHALL enter Task Output page
- **AND** the page SHALL participate in browser back/forward page history
- **AND** the page SHALL reset its task-output scroll position when opened

#### Scenario: Render current task output

- **GIVEN** a current build, test, or lint task exists
- **WHEN** Task Output page renders
- **THEN** the page SHALL show the task label, task status, command, and captured output lines
- **AND** the page SHALL expose contextual actions for copying, saving, stopping, rerunning, and returning

#### Scenario: Render empty current task output

- **GIVEN** no current task exists
- **WHEN** Task Output page renders
- **THEN** the page SHALL show an empty current-task output state
- **AND** it SHALL NOT synthesize output from task history

### Requirement: Task Output page scrolls independently

Task Output page SHALL maintain its own scroll state separate from Changed Files and File Detail.

#### Scenario: Scroll task output

- **GIVEN** Task Output page is visible with more captured output than fits on screen
- **WHEN** the user presses `up`, `down`, `pageup`, `pagedown`, `home`, or `end`
- **THEN** the browser SHALL update task-output scroll within valid bounds
- **AND** it SHALL NOT change selected file or File Detail scroll

### Requirement: Running task refresh preserves ordinary page stability

Running task output SHALL continue to avoid full-screen redraws on ordinary pages while keeping Task Output page live.

#### Scenario: Ordinary page uses Task Panel refresh

- **GIVEN** a task is running
- **AND** the user is on Changed Files, File Detail, Scope Home, Commit Picker, or Command Palette
- **WHEN** the browser receives an idle task tick
- **THEN** the browser SHALL try the existing Task Panel-only refresh path

#### Scenario: Task Output page redraws main content

- **GIVEN** a task is running
- **AND** the user is on Task Output page
- **WHEN** the browser receives an idle task tick
- **THEN** the browser SHALL schedule a full browser redraw
- **AND** it SHALL NOT use the Task Panel-only refresh path for that tick

### Requirement: Task Output page finds current output text

Task Output Page SHALL support text search over the current task's captured output.

#### Scenario: Find text in task output

- **GIVEN** Task Output Page is visible
- **AND** the current task output contains a line matching the query
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL store `TEXT` as the task output find query
- **AND** scroll Task Output Page to the first matching output line
- **AND** show status feedback for the match

#### Scenario: Find is case-insensitive and ignores ANSI style

- **GIVEN** Task Output Page is visible
- **AND** the current task output contains styled text whose plain form matches the query with different casing
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL treat that line as a match

#### Scenario: Find without current task

- **GIVEN** Task Output Page is visible
- **AND** no current task exists
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL keep the page and report that there is no task output to find

### Requirement: Task Output page repeats find matches

Task Output Page SHALL support repeat navigation for the most recent non-empty task output find query.

#### Scenario: Next and previous task output match

- **GIVEN** Task Output Page is visible
- **AND** a task output find query has been stored
- **WHEN** the user runs `next match` or `prev match`
- **THEN** the browser SHALL move to the next or previous matching output line with wraparound
- **AND** keep File Detail find state unchanged

#### Scenario: Repeat find without task output query

- **GIVEN** Task Output Page is visible
- **AND** no task output find query has been stored
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL report `Run find TEXT first.`

### Requirement: Browser extracts task output problems

The browser SHALL extract lightweight file-location problems from the current task output.

#### Scenario: Extract relative file anchor

- **GIVEN** the current task output contains `src/Foo.ets:12:3`
- **AND** `src/Foo.ets` exists in the repository
- **WHEN** Task Problems are built
- **THEN** the browser SHALL include a problem for `src/Foo.ets` at line `12` and column `3`

#### Scenario: Extract repo absolute file anchor

- **GIVEN** the current task output contains an absolute path under the repository root followed by `:line`
- **WHEN** Task Problems are built
- **THEN** the browser SHALL normalize the problem path to a repo-relative path

#### Scenario: Ignore non-repo anchors

- **GIVEN** the current task output contains a URL, missing file, or absolute path outside the repository
- **WHEN** Task Problems are built
- **THEN** the browser SHALL NOT include a problem for that anchor

### Requirement: Copy current task output tail

The browser SHALL support copying a compact tail of the current task output.

#### Scenario: Copy default task output tail
- **GIVEN** a current build/test/lint task with captured output lines
- **WHEN** the user runs `copy task tail`
- **THEN** the copied Markdown SHALL include task type, status, command, and only the last 40 captured output lines

#### Scenario: Copy custom-size task output tail
- **GIVEN** a current task with captured output lines
- **WHEN** the user runs `copy task tail 5`
- **THEN** the copied Markdown SHALL include only the last 5 captured output lines

#### Scenario: Copy task output tail without task
- **GIVEN** no current task exists
- **WHEN** the user runs `copy task tail`
- **THEN** the browser SHALL report that no task output tail can be copied
- **AND** it MUST NOT call the clipboard command

### Requirement: Save current task output tail

The browser SHALL support saving a compact tail of the current task output.

#### Scenario: Save default task output tail
- **GIVEN** a current task with captured output lines
- **WHEN** the user runs `save task tail`
- **THEN** the browser SHALL write tail Markdown to `.cr/handoff/task-output-tail.md`

#### Scenario: Save task output tail to custom path
- **GIVEN** a current task with captured output lines
- **WHEN** the user runs `save task tail tmp/tail.md`
- **THEN** the browser SHALL write tail Markdown to the requested path

#### Scenario: Save task output tail without task
- **GIVEN** no current task exists
- **WHEN** the user runs `save task tail`
- **THEN** the browser SHALL report that no task output tail can be saved
- **AND** it MUST NOT write a file

### Requirement: Task Output can open the first parsed problem

The Task Output page SHALL allow `view problem` to open the Source File page for
the first visible parsed task problem.

#### Scenario: View first parsed problem from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains repo-local parseable problems
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL open Source File at the first visible problem path and line
- **AND** Back SHALL return to Task Output

#### Scenario: No parsed problem exists

- **GIVEN** the browser is on Task Output
- **AND** the current task output has no visible parseable problems
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL stay on Task Output
- **AND** the status SHALL say no task problem can be viewed

### Requirement: Task Output supports selected problem navigation

The browser SHALL support moving the current parsed task-problem selection from
Task Output without requiring users to open Task Problems.

#### Scenario: Move to next parsed problem from Task Output

- **GIVEN** Task Output has multiple visible parsed problems
- **WHEN** the user runs `next problem`
- **THEN** the browser SHALL select the next visible problem
- **AND** keep the current page on Task Output.

#### Scenario: Move to previous parsed problem from Task Output

- **GIVEN** Task Output has multiple visible parsed problems and the second
  problem is selected
- **WHEN** the user runs `prev problem`
- **THEN** the browser SHALL select the previous visible problem
- **AND** keep the current page on Task Output.

### Requirement: Task Output shows selected problem status

Task Output SHALL show a compact selected-problem label when visible parsed
problems exist.

#### Scenario: Render selected problem label

- **GIVEN** Task Output has two visible parsed problems and the second problem is
  selected
- **WHEN** Task Output is rendered
- **THEN** the page SHALL show `Problem: 2/2` and the selected problem location.

### Requirement: Copy current Task Output match

The browser SHALL support `copy task match` when a current task has output and Task Output find text exists.

#### Scenario: Copy excerpt around current match

- **GIVEN** Task Output has captured lines
- **AND** the user has run `find TEXT`
- **AND** the current task output focus is on a matching line
- **WHEN** the user runs `copy task match`
- **THEN** the copied Markdown includes the query
- **AND** includes up to three lines before and after the focused line
- **AND** marks the focused line with `>`
- **AND** includes line numbers.

#### Scenario: Missing find text

- **GIVEN** Task Output has captured lines
- **AND** no Task Output find text exists
- **WHEN** the user runs `copy task match`
- **THEN** no clipboard write is attempted
- **AND** the browser reports `Run find TEXT first.`

### Requirement: Save current Task Output match

The browser SHALL support `save task match [PATH]` using the same excerpt as `copy task match`.

#### Scenario: Save default path

- **GIVEN** Task Output has captured lines
- **AND** the user has run `find TEXT`
- **WHEN** the user runs `save task match`
- **THEN** the excerpt is written to `.cr/handoff/task-output-match.md`.

### Requirement: Stop request grace period
`cr browse` SHALL track when a user requested a running background build to stop.

#### Scenario: User stops a running build
- **WHEN** a background build is running
- **AND** the user enters `stop` or `cancel`
- **THEN** the build state SHALL record the stop request time
- **AND** the build panel SHALL continue to show a stopping state until the process exits

### Requirement: Stop escalation is idempotent
Stop escalation SHALL execute at most once for a single build.

#### Scenario: Poll continues after escalation
- **WHEN** stop escalation has already sent a force-kill signal
- **AND** the build process has not been reaped yet
- **THEN** subsequent polling SHALL NOT send another force-kill signal
- **AND** subsequent polling SHALL NOT append duplicate escalation log lines

### Requirement: Background task runtime uses task naming
The browser's background task runtime SHALL use task-oriented names for the current task state and task lifecycle helpers.

#### Scenario: Current task state
- **WHEN** maintainers inspect `src/cr/ui/browser.py`
- **THEN** the current background task field SHALL be named as a task
- **AND** the state class SHALL be named `TaskState`
- **AND** the main lifecycle path SHALL NOT rely on `BuildState` as the runtime model

#### Scenario: Task lifecycle helpers
- **WHEN** maintainers inspect task lifecycle helpers
- **THEN** polling, recording, panel rendering, stopping, rerunning, output draining, and stop escalation SHALL use task-oriented helper names

### Requirement: User-visible task behavior remains stable
Task state naming changes SHALL preserve existing build/test/lint behavior.

#### Scenario: Existing task commands
- **WHEN** the user runs `build`, `test`, `lint`, `stop`, or `rerun`
- **THEN** the browser SHALL keep the same task behavior as before the rename

#### Scenario: Build command discovery
- **WHEN** build command discovery runs
- **THEN** build-specific default detection such as DouyinHarmony SHALL remain build-specific
- **AND** test/lint command discovery SHALL remain explicitly configured

### Requirement: Task runtime owns task lifecycle behavior
The system SHALL provide a browser task runtime module that owns command resolution, task state, background process lifecycle, output collection, stopping, stop escalation, rerun, foreground execution, and completion history.

#### Scenario: Command resolution remains unchanged
- **WHEN** the runtime resolves build, test, or lint commands
- **THEN** it SHALL preserve configured command handling, environment variable handling, missing-command behavior, and the DouyinHarmony build default

#### Scenario: Background task lifecycle remains unchanged
- **WHEN** the runtime starts and polls a configured task
- **THEN** it SHALL collect stdout lines, update return code, close stdout after completion, and append the same success, failure, stopped, or failed-to-start messages as before

#### Scenario: Stop and escalation behavior remains unchanged
- **WHEN** users stop a running task and the process does not exit inside the grace period
- **THEN** the runtime SHALL request process group termination first, then force kill the process group or parent process using the existing escalation behavior

#### Scenario: Rerun and history behavior remains unchanged
- **WHEN** users rerun the most recent completed task
- **THEN** the runtime SHALL rerun the same task kind, keep prior task history, and prevent starting a second process while one is running

### Requirement: Browser integrates through task runtime module
The browser SHALL call the task runtime module for task lifecycle operations while preserving Task Panel rendering and command behavior.

#### Scenario: Browser does not own task runtime helpers
- **WHEN** task lifecycle code is inspected
- **THEN** command resolution, start, stop, rerun, foreground execution, polling, output draining, and history recording SHALL live in `cr.ui.tasks`

#### Scenario: Task Panel rendering remains a browser concern
- **WHEN** the browser renders the bottom task panel
- **THEN** it SHALL continue to use TaskState and TaskRecord data without moving Browser Frame layout or terminal styling into the runtime module

#### Scenario: Existing task commands remain user-compatible
- **WHEN** users run `build`, `test`, `lint`, `stop`, or `rerun` in raw-key or line mode
- **THEN** the same foreground/background behavior, output panel behavior, and status history SHALL be preserved

### Requirement: Browser Frame module owns Task Panel presentation
The system SHALL render Task Panel lines from `TaskState`, `TaskRecord` history, and terminal style without depending on browser navigation state or review workspace state.

#### Scenario: Running task panel includes status command and output
- **WHEN** a task has a command, status, and captured output lines
- **THEN** the Browser Frame module SHALL render the panel divider, task label/status/command line, and the latest output lines within the requested height

#### Scenario: Task history is shown compactly
- **WHEN** task history is provided
- **THEN** the Browser Frame module SHALL render a compact recent-history line before the task output body

### Requirement: Browser Frame module owns partial Task Panel refresh
The system SHALL perform Task Panel-only refreshes without clearing the full browser screen and SHALL refuse partial refreshes when the cached frame is dirty, incomplete, or laid out for a different terminal size.

#### Scenario: Partial refresh updates only task panel rows
- **WHEN** the current task panel lines differ from the last rendered panel and the cached frame is complete and current
- **THEN** the Browser Frame module SHALL emit cursor-save, task-panel row positioning, per-row clearing, fitted task-panel lines, and cursor-restore sequences without emitting a full-screen clear

#### Scenario: Dirty frame refuses partial refresh
- **WHEN** the cached frame is marked dirty
- **THEN** the Browser Frame module SHALL emit no terminal output, keep the frame dirty, and report that no partial refresh occurred

#### Scenario: Unchanged panel emits nothing
- **WHEN** the newly rendered task panel lines match the cached panel
- **THEN** the Browser Frame module SHALL emit no terminal output and report that no partial refresh occurred

### Requirement: 复制当前任务输出
系统 SHALL 支持在浏览器内复制当前 Task Panel 的任务输出 handoff 文本。

#### Scenario: Copy running task output
- **WHEN** 当前存在正在运行的 build/test/lint task 且用户执行 `copy task`
- **THEN** 系统 SHALL 复制包含任务类型、状态、命令和当前输出行的文本

#### Scenario: Copy completed task output
- **WHEN** 当前 task 已完成且用户执行 `copy task`
- **THEN** 系统 SHALL 复制包含完成状态、命令和捕获输出行的文本

#### Scenario: Copy without task
- **WHEN** 当前没有 task 且用户执行 `copy task`
- **THEN** 系统 SHALL 报告没有 task output 可复制，并且 MUST NOT 调用剪贴板命令

### Requirement: 保存当前任务输出
系统 SHALL 支持在浏览器内保存当前 Task Panel 的任务输出 handoff 文本。

#### Scenario: Save task output to default path
- **WHEN** 当前存在 task 且用户执行 `save task`
- **THEN** 系统 SHALL 将 task output 写入 `.cr/handoff/task-output.md`

#### Scenario: Save task output to custom path
- **WHEN** 当前存在 task 且用户执行 `save task tmp/build.md`
- **THEN** 系统 SHALL 将 task output 写入用户指定路径

#### Scenario: Save without task
- **WHEN** 当前没有 task 且用户执行 `save task`
- **THEN** 系统 SHALL 报告没有 task output 可保存，并且 MUST NOT 写入文件
