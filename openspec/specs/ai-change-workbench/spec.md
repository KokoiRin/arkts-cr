# ai-change-workbench Specification

## Purpose
`cr` 是一个 terminal-first 的 AI change workbench，用于在 AI 辅助开发之后接管代码变更，支持人工 review、理解、验证、导航和上下文 handoff。

这份规格是当前产品行为的 canonical OpenSpec 归档。它把此前已经完成的 change-level specs 合并成一个长期维护的能力文档，后续工作应继续扩展这个主 workbench 规格，而不是累积彼此割裂的 delta specs。

## Requirements
### Requirement: CLI diff summarizes local changes
`cr diff` SHALL provide a scan-first summary of local Git changes without entering the interactive browser.

#### Scenario: Show changed-file statistics and tree
- **WHEN** the user runs `cr diff` in a repository with local changes
- **THEN** the CLI SHALL show Git diff statistics
- **AND** it SHALL render changed files as a directory tree with added/deleted counts and file status

#### Scenario: Filter CLI diff output
- **WHEN** the user passes `--code` or path arguments to `cr diff`
- **THEN** the CLI SHALL limit the visible changed files to matching code files or Git pathspecs

### Requirement: CLI outline summarizes a source file
`cr outline <file>` SHALL print a readable source summary for a single repo-local file.

#### Scenario: Show source purpose and symbols
- **WHEN** the user runs `cr outline <file>` for a supported ArkTS/TS-like file
- **THEN** the CLI SHALL print a compact purpose hint
- **AND** it SHALL print recognized class, struct, interface, function, method, field, enum, and related symbol rows where the lightweight parser can identify them

### Requirement: CLI review renders reviewable change context
`cr review` SHALL combine changed-file facts, source hints, and compact hunks into review-ready terminal output.

#### Scenario: Render default review output
- **WHEN** the user runs `cr review`
- **THEN** the CLI SHALL show a summary, changed-file tree, per-file facts, source purpose, modified-symbol hints, and compact diff hunks where available

#### Scenario: Control review output depth
- **WHEN** the user runs `cr review --summary`, `cr review --no-hunks`, or `cr review --context N`
- **THEN** the CLI SHALL preserve the selected review facts while changing how much hunk/source detail is rendered

#### Scenario: Emit structured and handoff formats
- **WHEN** the user runs `cr review --json` or `cr review --prompt`
- **THEN** the CLI SHALL emit machine-readable review data or prompt-ready Markdown without the normal terminal wrapper

### Requirement: CLI review supports review scopes
`cr review` SHALL let users choose the Git change scope from the command line.

#### Scenario: Review local and comparison scopes
- **WHEN** the user runs review with `--staged`, `--all`, `--base REF`, `--range OLD..NEW`, `--untracked`, or path arguments
- **THEN** the CLI SHALL render the requested scope without requiring checkout
- **AND** it SHALL keep deleted, renamed, binary, non-UTF-8, large, staged, unstaged, mixed, and untracked file facts readable

#### Scenario: Sort and pick large review output
- **WHEN** the user runs `cr review --sort risk`, `--sort churn`, `--sort path`, or `--pick N`
- **THEN** the CLI SHALL reorder or narrow the review output according to the selected scan strategy

### Requirement: CLI package exposes the cr command
The Python package SHALL expose `cr` as an offline-friendly console script.

#### Scenario: Install editable package without isolated build metadata
- **WHEN** the project is installed in editable mode in an environment without package-index access
- **THEN** `setup.py` SHALL expose the `cr=cr.cli:main` console script
- **AND** the project SHALL avoid build metadata that forces isolated dependency downloads for this package

### Requirement: Browse file list filtering
`cr browse` SHALL allow users to filter the interactive changed-file list by Git path during a review session.

#### Scenario: Apply a filter from the interactive list
- **WHEN** the user enters a non-empty filter query
- **THEN** the browser shows only changed files whose full Git path contains the query case-insensitively
- **AND** navigation, numeric selection, file opening, and next/previous commands operate on the filtered file list

#### Scenario: Show active filter status
- **WHEN** a filter is active
- **THEN** the browser displays the active filter query
- **AND** the browser displays the filtered match count relative to the total changed-file count
- **AND** the browser displays a clear-filter command

#### Scenario: Clear a filter
- **WHEN** a filter is active and the user clears it
- **THEN** the browser shows the full changed-file list again
- **AND** the selected index remains within the visible list

#### Scenario: Refresh with a filter
- **WHEN** a filter is active and the user refreshes the browser
- **THEN** the browser reloads changed files from Git
- **AND** reapplies the existing filter query
- **AND** clamps the selected index to the refreshed filtered list

### Requirement: Browse non-TTY compatibility
`cr browse` SHALL preserve line-oriented operation when stdin or stdout is not an interactive TTY.

#### Scenario: Filter from line mode
- **WHEN** `cr browse` runs in non-TTY mode and receives `/query` or `filter query`
- **THEN** the browser applies the query as a path filter
- **AND** subsequent line-mode selections operate on the filtered file list

#### Scenario: Existing line-mode commands keep working
- **WHEN** `cr browse` runs in non-TTY mode
- **THEN** existing commands for list, numeric selection, next, previous, refresh, open, help, and quit continue to work

### Requirement: Browser module locality
Interactive browse behavior SHALL be owned by a dedicated browser module instead of the CLI argument parsing module.

#### Scenario: CLI dispatches to browser module
- **WHEN** the `browse` command is invoked
- **THEN** the CLI delegates browser execution to the browser module through a small function interface
- **AND** browse state transitions and rendering are implemented outside the CLI parser module

### Requirement: Browser screen regions
`cr browse` SHALL render interactive TTY sessions using stable screen regions for content, background task output, and command input.

#### Scenario: Render with no background task
- **WHEN** the browser has no active build panel
- **THEN** the main content region SHALL use the available terminal rows above the input prompt
- **AND** the input prompt SHALL remain on the final terminal row

#### Scenario: Render with a build panel
- **WHEN** a build panel is present
- **THEN** the main content region SHALL shrink to leave room for the build panel
- **AND** the build panel SHALL render above the input prompt
- **AND** the input prompt SHALL remain below the build panel

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

### Requirement: Raw-key commands do not scroll the screen
`cr browse` SHALL treat raw-key input as command events instead of terminal text output.

#### Scenario: User presses a navigation key
- **WHEN** raw-key mode reads a navigation key, selection key, or page key
- **THEN** command reading SHALL NOT print an extra newline
- **AND** the next visible change SHALL come from fixed-area redraw or isolated panel refresh

#### Scenario: User enters line input intentionally
- **WHEN** the user opens filter input or command input
- **THEN** the browser MAY show a dedicated line prompt for that input
- **AND** returning from that input SHALL restore fixed-region rendering on the next redraw

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

### Requirement: Browser displays active review scope
`cr browse` SHALL display the active review scope in the interactive browser context area.

#### Scenario: Default worktree scope
- **WHEN** the browser is reviewing default unstaged worktree changes
- **THEN** the browser SHALL display `Scope: worktree`

#### Scenario: Non-default local scopes
- **WHEN** the browser is reviewing staged changes
- **THEN** the browser SHALL display `Scope: staged`
- **WHEN** the browser is reviewing combined local changes
- **THEN** the browser SHALL display `Scope: all local changes`

#### Scenario: Ref comparison scopes
- **WHEN** the browser is reviewing changes from a base ref
- **THEN** the browser SHALL display `Scope: base <ref>`
- **WHEN** the browser is reviewing an explicit ref range
- **THEN** the browser SHALL display `Scope: range <old>..<new>`

#### Scenario: Commit scopes
- **WHEN** the browser is showing recent commits
- **THEN** the browser SHALL display `Scope: recent commits`
- **WHEN** the browser is reviewing a selected commit
- **THEN** the browser SHALL display `Scope: commit <short-hash>`

### Requirement: Browser switches review scope in-session
`cr browse` SHALL allow users to switch review scopes from the command prompt without restarting the browser.

#### Scenario: Switch between local scopes
- **WHEN** the user enters `staged`
- **THEN** the browser SHALL reload changed files for staged changes
- **AND** display `Scope: staged`
- **WHEN** the user enters `all`
- **THEN** the browser SHALL reload changed files for combined local changes
- **AND** display `Scope: all local changes`
- **WHEN** the user enters `worktree`
- **THEN** the browser SHALL reload changed files for default worktree changes
- **AND** display `Scope: worktree`

#### Scenario: Switch to ref comparison scopes
- **WHEN** the user enters `base <ref>`
- **THEN** the browser SHALL reload changed files for that base ref comparison
- **AND** display `Scope: base <ref>`
- **WHEN** the user enters `range <old>..<new>`
- **THEN** the browser SHALL reload changed files for that explicit ref range
- **AND** display `Scope: range <old>..<new>`

#### Scenario: Scope switch resets view-local state
- **WHEN** the user switches review scope
- **THEN** the browser SHALL clear the active file filter
- **AND** reset selection, file scroll, list scroll, and render caches

### Requirement: Browser command list entry points
`cr browse` SHALL provide in-session entry points for users to discover command prompt commands.

#### Scenario: Open command list from line mode
- **WHEN** the browser receives `commands`, `cmds`, or `help commands`
- **THEN** the browser SHALL show a command list
- **AND** the session SHALL remain open

#### Scenario: Open command list from raw command prompt
- **WHEN** the browser is in raw-key mode and the user opens `:` command input
- **AND** the user submits empty input or `?`
- **THEN** the browser SHALL show a command list

### Requirement: Browser command list content
The command list SHALL group available browser commands by purpose.

#### Scenario: Show grouped commands
- **WHEN** the command list is shown
- **THEN** it SHALL include navigation commands
- **AND** it SHALL include review scope commands
- **AND** it SHALL include build task commands
- **AND** it SHALL include file/session commands

#### Scenario: Return from command list
- **WHEN** the command list is shown and the user enters `b` or `back`
- **THEN** the browser SHALL return to the changed-file list
- **AND** active build task output SHALL remain available in the bottom task panel

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

### Requirement: Stop request grace period
`cr browse` SHALL track when a user requested a running background build to stop.

#### Scenario: User stops a running build
- **WHEN** a background build is running
- **AND** the user enters `stop` or `cancel`
- **THEN** the build state SHALL record the stop request time
- **AND** the build panel SHALL continue to show a stopping state until the process exits

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

### Requirement: Stop escalation is idempotent
Stop escalation SHALL execute at most once for a single build.

#### Scenario: Poll continues after escalation
- **WHEN** stop escalation has already sent a force-kill signal
- **AND** the build process has not been reaped yet
- **THEN** subsequent polling SHALL NOT send another force-kill signal
- **AND** subsequent polling SHALL NOT append duplicate escalation log lines

### Requirement: Save browser workspace on exit
`cr browse` SHALL save the current browser review workspace on clean session exit.

#### Scenario: Save changed-file workspace
- **WHEN** a user exits `cr browse`
- **THEN** the browser SHALL save the active review scope
- **AND** it SHALL save the active file filter
- **AND** it SHALL save the selected changed file path and selected index
- **AND** it SHALL save whether the user was on the file list or file diff layer

### Requirement: Restore default browser workspace
Default `cr browse` SHALL restore the saved browser review workspace when no explicit scope or pathspec overrides are provided.

#### Scenario: Restore selected filtered file
- **GIVEN** a saved browser workspace with a filter and selected path
- **WHEN** the user starts default `cr browse`
- **THEN** the browser SHALL restore the saved scope before loading changes
- **AND** it SHALL restore the filter
- **AND** it SHALL select the saved path when that path is still visible
- **AND** it SHALL restore the saved list or file layer

#### Scenario: Saved path is no longer visible
- **GIVEN** a saved selected path that is no longer present in current changes
- **WHEN** the user starts default `cr browse`
- **THEN** the browser SHALL fall back to the saved index
- **AND** it SHALL clamp the selection to the current visible changes
- **AND** it SHALL NOT crash

### Requirement: Explicit CLI intent wins
Saved browser workspace SHALL NOT override explicit CLI scope or pathspec input.

#### Scenario: User passes explicit scope
- **GIVEN** a saved browser workspace
- **WHEN** the user starts `cr browse --staged`, `--all`, `--base REF`, `--range OLD..NEW`, or `--untracked`
- **THEN** the browser SHALL use the CLI-provided scope
- **AND** it SHALL ignore the saved scope for that session

#### Scenario: User passes pathspec
- **GIVEN** a saved browser workspace
- **WHEN** the user starts `cr browse src/pages`
- **THEN** the browser SHALL use the CLI-provided pathspec
- **AND** it SHALL ignore the saved filter and selected path for that session

### Requirement: Invalid saved workspace is ignored
`cr browse` SHALL ignore missing, unreadable, malformed, or unsupported workspace state files without failing startup.

#### Scenario: Saved workspace file is malformed
- **GIVEN** the saved browser workspace file contains malformed JSON
- **WHEN** the user starts default `cr browse`
- **THEN** the browser SHALL ignore the saved file
- **AND** it SHALL continue with normal default startup

### Requirement: Mark browse file progress
`cr browse` SHALL allow users to mark the selected changed file as seen and later remove that mark.

#### Scenario: Mark selected file seen
- **WHEN** a changed file is selected in `cr browse`
- **AND** the user enters `m`, `seen`, or `done`
- **THEN** the browser SHALL add that file path to the seen set
- **AND** the file list SHALL show that file as seen

#### Scenario: Unmark selected file
- **WHEN** a seen changed file is selected in `cr browse`
- **AND** the user enters `todo`, `unseen`, or `unmark`
- **THEN** the browser SHALL remove that file path from the seen set
- **AND** the file list SHALL show that file as not seen

### Requirement: Show remaining browse files
`cr browse` SHALL allow users to focus on files that are not marked seen.

#### Scenario: Remaining-only view
- **WHEN** the user enters `remaining`
- **THEN** the browser SHALL show only changed files not in the seen set
- **AND** navigation and numeric selection SHALL operate on that remaining list

#### Scenario: Return to all files
- **WHEN** the user enters `allfiles` or `show all`
- **THEN** the browser SHALL show all changed files again
- **AND** existing seen markers SHALL remain intact

### Requirement: Persist browse progress
Browser progress markers SHALL persist with the browser workspace state.

#### Scenario: Save browse progress on exit
- **WHEN** a user exits `cr browse`
- **THEN** the browser workspace state SHALL include seen paths
- **AND** it SHALL include the remaining-only view flag

#### Scenario: Restore browse progress
- **GIVEN** saved seen paths and remaining-only flag
- **WHEN** the user starts default `cr browse`
- **THEN** the browser SHALL restore seen markers
- **AND** it SHALL restore the remaining-only view flag

### Requirement: Render browse progress
`cr browse` SHALL display review progress in list and file views.

#### Scenario: File list shows progress
- **WHEN** the browser shows the changed-file list
- **THEN** it SHALL show the number of seen files and total files
- **AND** each changed-file row SHALL indicate whether that file is seen

#### Scenario: File diff shows progress
- **WHEN** the browser shows a single file diff
- **THEN** the file header SHALL indicate whether the current file is seen or todo

### Requirement: Browser frame owns raw-key screen rendering
`cr browse` SHALL coordinate raw-key full redraws, task-panel partial refreshes, and prompt placement through a single browser frame state.

#### Scenario: Full redraw records the current frame
- **WHEN** raw-key browser mode performs a full screen redraw
- **THEN** the browser SHALL record the layout used for that redraw
- **AND** it SHALL record that a complete frame exists
- **AND** it SHALL record the task-panel contents rendered in that frame

#### Scenario: User command redraw replaces the previous frame
- **WHEN** a user command changes selection, mode, scope, filter, or scroll state
- **THEN** the next visible update SHALL be a full browser frame redraw
- **AND** any later partial task-panel refresh SHALL use the latest frame layout

### Requirement: Task-panel partial refresh is frame-safe
`cr browse` SHALL only perform task-panel partial refreshes when the last complete frame still matches the current screen layout.

#### Scenario: Task output changes with a valid frame
- **GIVEN** a complete browser frame has been rendered
- **AND** the current layout matches that frame
- **WHEN** build output changes while the user is idle
- **THEN** the browser SHALL update only the task-panel rows
- **AND** it SHALL preserve the command prompt cursor position
- **AND** it SHALL NOT clear the full screen

#### Scenario: Task output changes without a valid frame
- **GIVEN** no complete frame exists or the layout has changed since the last frame
- **WHEN** build output changes while the user is idle
- **THEN** the browser SHALL NOT write a partial task-panel update
- **AND** it SHALL request a full browser frame redraw

#### Scenario: Task output is unchanged
- **GIVEN** a complete browser frame has been rendered
- **WHEN** the task-panel text is unchanged
- **THEN** the browser SHALL NOT write a duplicate task-panel update

### Requirement: Temporary line input restores fixed frame
`cr browse` SHALL restore the fixed browser frame after temporary command or filter line input.

#### Scenario: Command prompt returns
- **WHEN** the user opens `:` command input and submits or cancels it
- **THEN** the browser SHALL mark the frame dirty
- **AND** the next raw-key visual update SHALL be a full browser frame redraw

#### Scenario: Filter prompt returns
- **WHEN** the user opens `/` filter input and submits or cancels it
- **THEN** the browser SHALL mark the frame dirty
- **AND** the next raw-key visual update SHALL be a full browser frame redraw

### Requirement: Command palette lists executable commands
`cr browse` SHALL provide an executable command palette in commands mode.

#### Scenario: Open command palette
- **WHEN** the user enters `commands`, `cmds`, or `help commands`
- **THEN** the browser SHALL enter commands mode
- **AND** it SHALL show commands that can be executed directly from the palette

#### Scenario: Non-executable command templates are excluded
- **WHEN** the browser renders the executable command palette
- **THEN** parameter templates such as `base REF` and `range OLD..NEW` SHALL NOT be executable palette rows
- **AND** users SHALL still be able to type those commands through the normal command prompt

### Requirement: Command palette supports keyboard selection
`cr browse` SHALL let raw-key users move within the command palette without changing the selected review file.

#### Scenario: Move selected palette command
- **GIVEN** commands mode is active
- **WHEN** the user presses ↑/↓ or j/k
- **THEN** the selected palette command SHALL move within the executable command list
- **AND** the selected changed file SHALL remain unchanged

#### Scenario: Return to file list
- **GIVEN** commands mode is active
- **WHEN** the user presses b or ←
- **THEN** the browser SHALL return to list mode
- **AND** the selected changed file SHALL remain unchanged

### Requirement: Command palette executes selected commands
`cr browse` SHALL execute the selected palette command when users press Enter in commands mode.

#### Scenario: Execute selected command
- **GIVEN** commands mode is active
- **AND** a palette command is selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute that command through the same command handling path as typed commands

#### Scenario: Enter does not open a file from commands mode
- **GIVEN** commands mode is active
- **AND** the review has visible changed files
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute the selected palette command
- **AND** it SHALL NOT open the selected changed file unless the selected palette command is an explicit file-opening command

### Requirement: Command palette filters executable commands
`cr browse` SHALL allow users to filter executable command palette entries.

#### Scenario: Filter palette commands
- **GIVEN** commands mode is active
- **WHEN** the user enters a command palette filter
- **THEN** the palette SHALL show only executable commands whose group, label, command, or description contains the filter text case-insensitively
- **AND** the selected palette row SHALL clamp to the filtered results

#### Scenario: Empty palette filter result
- **GIVEN** commands mode is active
- **WHEN** the command palette filter matches no executable commands
- **THEN** the palette SHALL show an empty-result message
- **AND** pressing Enter SHALL NOT execute a stale command

### Requirement: Command palette filter is independent from file filter
Command palette search SHALL NOT modify file path filtering.

#### Scenario: Search command palette
- **GIVEN** commands mode is active
- **WHEN** the user presses `/` and enters a command filter
- **THEN** the browser SHALL update the command palette filter
- **AND** it SHALL NOT update the changed-file path filter

#### Scenario: Clear command palette filter
- **GIVEN** commands mode is active
- **AND** the changed-file path filter is set
- **AND** the command palette filter is set
- **WHEN** the user enters `c` or `clear`
- **THEN** the browser SHALL clear the command palette filter
- **AND** it SHALL keep the changed-file path filter unchanged

### Requirement: Filtered palette commands execute normally
Filtered command palette results SHALL execute through the existing command handling path.

#### Scenario: Execute filtered command
- **GIVEN** commands mode is active
- **AND** the command palette filter leaves a matching executable command selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute that filtered command
- **AND** it SHALL use the same command handling path as a typed command

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

### Requirement: Browser uses explicit page layers
`cr browse` raw-key mode SHALL render the screen as a single frame composed of context/status, main content, background task panel, and input prompt layers.

#### Scenario: Full redraw with a running task
- **GIVEN** a background build exists
- **WHEN** the browser performs a full redraw
- **THEN** it SHALL render context/status above the main content
- **AND** it SHALL render the task panel above the final prompt row
- **AND** it SHALL place the prompt on the final terminal row

### Requirement: Raw-key feedback stays inside the browser frame
Raw-key browser actions SHALL NOT print ordinary feedback outside the fixed frame.

#### Scenario: Open selected file in raw-key mode
- **WHEN** the user opens a selected file
- **THEN** the browser SHALL show the result in the context/status layer
- **AND** it SHALL schedule a full redraw
- **AND** it SHALL NOT append feedback below the prompt

#### Scenario: Invalid selection in raw-key mode
- **WHEN** the user enters an invalid numeric selection
- **THEN** the browser SHALL show the validation message in the context/status layer
- **AND** it SHALL schedule a full redraw

#### Scenario: Unknown command in raw-key mode
- **WHEN** the user enters an unknown command
- **THEN** the browser SHALL show a compact unknown-command message in the context/status layer
- **AND** it SHALL schedule a full redraw

### Requirement: Task panel partial refresh respects frame ownership
Background task partial refresh SHALL only write to the task panel when the existing browser frame is complete and still owns the terminal layout.

#### Scenario: Frame is incomplete or dirty
- **GIVEN** the browser frame is incomplete or dirty
- **WHEN** build output changes
- **THEN** the task panel partial refresh SHALL refuse to write
- **AND** the browser SHALL perform a later full redraw

#### Scenario: Status message is pending
- **GIVEN** a raw-key action has produced a status message that has not been rendered by a full redraw
- **WHEN** build output changes
- **THEN** the task panel partial refresh SHALL refuse to write over the stale frame

### Requirement: Browser context renders product navigation breadcrumbs
`cr browse` SHALL render the product navigation hierarchy in the context/status layer.

#### Scenario: Changed Files layer
- **GIVEN** the browser is showing the changed-file tree for a Review Scope
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: <scope> > Files`

#### Scenario: File Detail layer
- **GIVEN** the browser is showing a selected file detail
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: <scope> > Files > <path>`

#### Scenario: Commit picker layer
- **GIVEN** the browser is showing recent commits before a commit is selected
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: recent commits`
- **AND** it SHALL NOT append `> Files`

#### Scenario: Selected commit files
- **GIVEN** the user selected a commit as the Review Scope
- **WHEN** the browser shows that commit's changed-file tree
- **THEN** the context/status layer SHALL show `Scope: commit <short-sha> > Files`

#### Scenario: Status message
- **GIVEN** a raw-key action has produced a status message
- **WHEN** the context/status layer is rendered
- **THEN** the status message SHALL appear after the breadcrumb

### Requirement: Browser provides a Review Scope Home
`cr browse` SHALL provide a first-level Review Scope Home page.

#### Scenario: Open Scope Home
- **WHEN** the user runs `scopes` or `scope`
- **THEN** the browser SHALL show a Scope Home page
- **AND** the page SHALL list worktree, staged, all local changes, recent commits, base ref, and explicit range entries

#### Scenario: Scope Home breadcrumb
- **GIVEN** Scope Home is visible
- **WHEN** the browser renders the context/status layer
- **THEN** it SHALL show `Scope: scope home`
- **AND** it SHALL NOT append `> Files`

#### Scenario: Select executable scope entry
- **GIVEN** Scope Home is visible
- **WHEN** the user selects an executable scope entry and presses Enter
- **THEN** the browser SHALL enter that Review Scope using the existing scope switching behavior

#### Scenario: Parameterized scope entries
- **GIVEN** Scope Home is visible
- **WHEN** the page renders base ref and explicit range entries
- **THEN** those entries SHALL explain the command form the user should type
- **AND** they SHALL NOT pretend to execute without a parameter

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

### Requirement: Task commands are discoverable
The command help and command palette SHALL expose build, test, lint, stop, and rerun commands.

#### Scenario: Open command palette
- **WHEN** the user opens the command palette
- **THEN** executable entries SHALL include build, test, lint, stop, and rerun task actions

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

### Requirement: Browser exposes an explicit page model
The browser SHALL expose explicit page names for the existing product pages.

#### Scenario: Page names exist
- **WHEN** maintainers inspect the browser page model
- **THEN** it SHALL include named pages for scope home, commit picker, changed files, file detail, and command palette
- **AND** those names SHALL map to the existing persisted/prompt string values

#### Scenario: Browser state owns current page
- **WHEN** a new browser state is created
- **THEN** its current page SHALL be Changed Files
- **AND** `mode` compatibility SHALL read and write the same current page

### Requirement: Existing browser behavior remains stable
Adding the page model SHALL preserve existing user-visible behavior.

#### Scenario: Existing prompts and persistence
- **WHEN** the browser renders prompts or saves workspace state
- **THEN** it SHALL keep the existing prompt strings and persisted mode values

#### Scenario: Existing navigation
- **WHEN** the user navigates between scope home, commit picker, changed files, file detail, and command palette
- **THEN** behavior SHALL remain the same as before the page model

### Requirement: Browser navigation owns page transition rules
The browser SHALL route page transition rules through a dedicated navigation module instead of scattering raw page assignments through the main browse loop.

#### Scenario: Navigation opens changed files
- **WHEN** the browser returns to Changed Files from another page
- **THEN** the current page SHALL become Changed Files
- **AND** file detail scroll SHALL reset

#### Scenario: Navigation opens file detail
- **WHEN** the browser opens File Detail for the selected changed file
- **THEN** the current page SHALL become File Detail
- **AND** file detail scroll SHALL reset

#### Scenario: Navigation opens cross-layer pages
- **WHEN** the browser opens Scope Home, Commit Picker, or Command Palette
- **THEN** the current page SHALL match the requested page
- **AND** page-local selection or scroll SHALL reset where existing behavior already resets it

### Requirement: Existing browser navigation behavior remains stable
Introducing the navigation module SHALL preserve the existing user-visible browse behavior.

#### Scenario: Back behavior remains hierarchy-aware
- **WHEN** the user goes back from Command Palette, Scope Home, or File Detail
- **THEN** the browser SHALL return to Changed Files
- **AND** file detail scroll SHALL reset

#### Scenario: Selected commit back behavior remains compatible
- **WHEN** the user is in a selected commit scope and goes back from Changed Files
- **THEN** the browser SHALL return to Commit Picker as before

#### Scenario: Persistence remains compatible
- **WHEN** browser workspace state is saved or restored
- **THEN** persisted `mode` values SHALL remain the existing string values

### Requirement: Review workspace owns active scope and changed files
The browser SHALL use a dedicated review workspace module to own active Review Scope state and changed-file loading behavior.

#### Scenario: Workspace loads current scope
- **WHEN** a review workspace is created from the current browser arguments
- **THEN** it SHALL load sorted changed files through the existing review selection path
- **AND** it SHALL expose the same changed files to the browser UI

#### Scenario: Workspace switches local scopes
- **WHEN** the browser switches to worktree, staged, all local changes, base, or range scope
- **THEN** the workspace SHALL update the active scope
- **AND** it SHALL reload changed files
- **AND** it SHALL reset selected commit, previous scope, filter, selection, and scroll state as existing behavior does

#### Scenario: Workspace selects a commit scope
- **WHEN** the browser selects a recent commit
- **THEN** the workspace SHALL capture the previous scope if needed
- **AND** it SHALL switch active scope to that commit's ref range
- **AND** it SHALL reload changed files and return to Changed Files

### Requirement: Review workspace preserves existing persistence behavior
Introducing the review workspace module SHALL preserve browser workspace state compatibility.

#### Scenario: Workspace state is saved
- **WHEN** the browser saves workspace state on clean exit
- **THEN** the saved JSON SHALL keep the same version, scope, filter, selected path/index, mode, seen paths, and remaining-only fields

#### Scenario: Workspace state is restored
- **WHEN** compatible workspace state exists and no explicit scope override is passed
- **THEN** the browser SHALL restore the same scope, filter, selected file, progress markers, and list/file page as before

### Requirement: UI-only browser state remains outside review workspace
The review workspace module SHALL NOT own terminal rendering, background tasks, command palette filtering, raw-key input, or editor handoff.

#### Scenario: Task panel remains browser-owned
- **WHEN** the workspace switches review scope
- **THEN** current background task state SHALL remain attached to the browser session
- **AND** it SHALL NOT be persisted as workspace state

### Requirement: Browser commands parse to stable actions
The browser SHALL parse command input into stable command actions before executing browser behavior.

#### Scenario: Alias commands map to the same action
- **WHEN** the parser receives aliases such as `q`, `quit`, or `exit`
- **THEN** it SHALL return the same quit action

#### Scenario: Parameter commands expose values
- **WHEN** the parser receives `base REF`, `range OLD..NEW`, `filter QUERY`, `/QUERY`, or a numeric choice
- **THEN** it SHALL return the matching action
- **AND** it SHALL expose the parsed value without requiring the execution layer to parse the raw string again

#### Scenario: Unknown commands remain explicit
- **WHEN** the parser receives an unsupported command
- **THEN** it SHALL return an unknown action
- **AND** the browser SHALL keep existing unknown-command feedback behavior

### Requirement: Existing browser command behavior remains stable
Introducing command dispatch SHALL preserve existing user-visible behavior.

#### Scenario: Existing commands still execute
- **WHEN** the user runs existing navigation, scope, task, filter, progress, file, and session commands
- **THEN** they SHALL behave as before command dispatch deepening

#### Scenario: Raw-key prompt sentinels remain browser-owned
- **WHEN** the command reader returns tick, eof, or interrupt sentinels
- **THEN** the browser loop SHALL keep existing lifecycle handling
- **AND** command dispatch SHALL NOT replace task-panel tick or clean-exit behavior

### Requirement: Parsed command actions execute through one action execution interface
The system SHALL execute parsed browser command actions through a dedicated action execution interface instead of keeping every action branch directly in `run_browser`.

#### Scenario: Run loop delegates executable actions
- **WHEN** `run_browser` has resolved temporary prompt input and parsed a browser command
- **THEN** it SHALL call the action execution interface with the parsed command and use the returned loop control result

#### Scenario: Executor reports redraw needs
- **WHEN** an action changes visible browser state
- **THEN** the execution interface SHALL return a result that asks the run loop to redraw

#### Scenario: Executor reports quit intent
- **WHEN** the parsed command is quit
- **THEN** the execution interface SHALL return an exit code and the run loop SHALL remain responsible for saving workspace state before returning that code

### Requirement: Action execution preserves existing behavior
The system SHALL preserve the existing browser command behavior while moving execution behind the action execution interface.

#### Scenario: Scope and navigation actions behave as before
- **WHEN** users run existing scope or navigation commands such as `staged`, `all`, `base REF`, `range OLD..NEW`, `g`, `b`, `enter`, `n`, or `p`
- **THEN** the same review scope, page, selection, and redraw behavior SHALL be preserved

#### Scenario: Task actions behave as before
- **WHEN** users run existing task commands such as `build`, `test`, `lint`, `stop`, or `rerun`
- **THEN** the same foreground or background task behavior SHALL be preserved for line mode and raw-key mode

#### Scenario: Unknown command feedback behaves as before
- **WHEN** users enter an unknown command
- **THEN** the same raw-key or line-mode feedback text SHALL be produced through the browser feedback path

### Requirement: Input prompt protocol remains outside normal action execution
The system SHALL keep temporary input prompt handling at the run loop input edge.

#### Scenario: Filter prompt is resolved before normal execution
- **WHEN** the parsed command requests the filter prompt
- **THEN** the run loop SHALL read the filter query, update the correct filter, and not route the prompt action through normal action execution

#### Scenario: Command prompt is resolved before normal execution
- **WHEN** the parsed command requests the command prompt
- **THEN** the run loop SHALL read and normalize the command query, parse the resulting command, and then route only the resulting executable action through normal action execution

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

### Requirement: Browser task behavior remains compatible
The browser SHALL continue to use build/test/lint commands through Task Runtime without changing task panel rendering or command interaction.

#### Scenario: Existing task commands use presets transparently
- **WHEN** users run `build`, `test`, or `lint` in raw-key or line mode
- **THEN** the browser SHALL use the resolved task command from Task Runtime and preserve foreground/background behavior

### Requirement: Browser copies selected file path
The browser SHALL provide a command action that copies the selected changed file's repository-relative path.

#### Scenario: Copy selected path
- **WHEN** the user runs `copy path` with a changed file selected
- **THEN** the browser SHALL copy that file's repo-relative path
- **AND** show feedback through the existing browser message/status area

#### Scenario: Copy path with no file
- **WHEN** the user runs `copy path` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without changing page state

### Requirement: Browser copies selected file anchor
The browser SHALL provide a command action that copies a review anchor for the selected changed file.

#### Scenario: Copy selected anchor with first changed line
- **WHEN** the selected file has a first changed line
- **THEN** the copied anchor SHALL be `path:line`

#### Scenario: Copy selected anchor without first changed line
- **WHEN** the selected file has no first changed line
- **THEN** the copied anchor SHALL fall back to the repo-relative path

### Requirement: Browser reveals selected file
The browser SHALL provide a command action that reveals the selected changed file in the OS file browser when supported.

#### Scenario: Reveal selected file
- **WHEN** the user runs `reveal` with a changed file selected
- **THEN** the browser SHALL launch the supported OS reveal command for that repository file
- **AND** show feedback through the existing browser message/status area

### Requirement: File actions use browser command infrastructure
The browser SHALL expose file actions through the existing parser, command palette, and action executor.

#### Scenario: Command palette lists file actions
- **WHEN** the command palette is rendered
- **THEN** `copy path`, `copy anchor`, and `reveal` SHALL appear as executable file commands

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

### Requirement: Browser records page history
The browser SHALL record in-session page transitions as navigation history.

#### Scenario: Open file detail then go back
- **WHEN** the user opens File Detail from Changed Files
- **AND** then runs `back`
- **THEN** the browser SHALL return to the prior Changed Files state including selected file and list scroll

#### Scenario: Open command palette then go back
- **WHEN** the user opens Command Palette from another browser page
- **AND** then runs `back`
- **THEN** the browser SHALL return to the page that opened Command Palette

### Requirement: Browser supports forward navigation
The browser SHALL provide a `forward` command that restores the page most recently left by `back`.

#### Scenario: Back then forward
- **WHEN** the user opens File Detail, runs `back`, and then runs `forward`
- **THEN** the browser SHALL return to File Detail with its local scroll state restored

#### Scenario: New branch clears forward history
- **WHEN** the user goes back and then opens a different page
- **THEN** the browser SHALL clear forward history

### Requirement: Scope switching resets page history
The browser SHALL treat page history as scoped to the current Review Scope.

#### Scenario: Switch review scope
- **WHEN** the user switches Review Scope
- **THEN** the browser SHALL reset back/forward page history

### Requirement: Existing fallback back behavior remains
The browser SHALL keep the existing hierarchy-aware fallback when no page history is available.

#### Scenario: Back with no history
- **WHEN** no page history is available
- **THEN** `back` SHALL preserve the existing fallback behavior for File Detail, Command Palette, Scope Home, selected commit scopes, and Changed Files

### Requirement: Browser supports configured copy command
The browser SHALL allow users to configure the command used by `copy path` and `copy anchor`.

#### Scenario: Copy command from CLI argument
- **WHEN** the user provides `--copy-cmd`
- **THEN** `copy path` and `copy anchor` SHALL use that command
- **AND** SHALL provide the copied text to the command

#### Scenario: Copy command from environment
- **WHEN** `CR_COPY_CMD` is set and no CLI copy command is provided
- **THEN** copy actions SHALL use `CR_COPY_CMD`

### Requirement: Browser supports configured reveal command
The browser SHALL allow users to configure the command used by `reveal`.

#### Scenario: Reveal command from CLI argument
- **WHEN** the user provides `--reveal-cmd`
- **THEN** `reveal` SHALL use that command for the selected repository file

#### Scenario: Reveal command from environment
- **WHEN** `CR_REVEAL_CMD` is set and no CLI reveal command is provided
- **THEN** reveal SHALL use `CR_REVEAL_CMD`

### Requirement: Built-in file action fallbacks remain
The browser SHALL preserve built-in platform copy and reveal fallbacks when no configured command is present.

#### Scenario: No configured file action command
- **WHEN** no CLI argument or environment variable is set for a file action
- **THEN** the existing platform fallback behavior SHALL remain available

### Requirement: File action configuration stays behind file action helpers
The browser SHALL keep command-template parsing and subprocess execution inside `cr.ui.file_actions`.

#### Scenario: Browser executes configured file action
- **WHEN** the browser executes copy or reveal
- **THEN** browser action execution SHALL pass configuration to the file action helper without parsing the template itself

### Requirement: Browser shows task preset schema help
The browser SHALL provide a `tasks help` command that explains the supported
`.cr/tasks.json` preset format.

#### Scenario: Show preset format
- **WHEN** the user runs `tasks help`
- **THEN** the browser SHALL show the preset file path
- **AND** SHALL list the supported task keys `build`, `test`, and `lint`
- **AND** SHALL show that each value is a command string
- **AND** SHALL include a compact JSON example
- **AND** SHALL NOT start or stop any task process

### Requirement: Task preset help preserves diagnostics semantics
The browser SHALL keep task source diagnostics and preset format help as
separate commands.

#### Scenario: Show task sources
- **WHEN** the user runs `tasks`
- **THEN** the browser SHALL show command source diagnostics
- **AND** SHALL NOT show the full preset format help

### Requirement: Malformed preset diagnostics point to schema help
Task Runtime SHALL keep malformed `.cr/tasks.json` non-fatal while offering a
concise next step.

#### Scenario: Invalid preset file
- **WHEN** `.cr/tasks.json` is malformed
- **THEN** task diagnostics SHALL include the preset warning
- **AND** SHALL include a hint to run `tasks help`

### Requirement: Browser records per-file review notes
The browser SHALL let users set or replace one note for the currently selected changed file.

#### Scenario: Set selected file note
- **WHEN** the user runs `note check lifecycle edge case`
- **AND** a changed file is selected
- **THEN** the selected file SHALL store the note text `check lifecycle edge case`
- **AND** the browser SHALL remain in the current review context
- **AND** SHALL NOT start or stop any task process

### Requirement: Browser clears selected file notes
The browser SHALL let users clear the currently selected file note without editing persisted JSON by hand.

#### Scenario: Clear selected file note
- **WHEN** the selected file already has a note
- **AND** the user runs `note`
- **THEN** the selected file note SHALL be removed
- **AND** the browser SHALL report that the note was cleared

### Requirement: Browser renders review notes in review layers
The browser SHALL surface review notes where users scan and read changed files.

#### Scenario: Show note in changed files and file detail
- **WHEN** a changed file has a note
- **THEN** the Changed Files row SHALL show a compact note marker
- **AND** the File Detail header area SHALL show the full note text

### Requirement: Browser persists review notes with workspace state
The browser SHALL save and restore per-file review notes in the default workspace state.

#### Scenario: Restore saved note
- **WHEN** `.git/cr/browse-state.json` contains `review_notes` for a changed file
- **AND** the next default browser session restores workspace state
- **THEN** the restored browser state SHALL include that file note
- **AND** task history SHALL remain excluded from workspace persistence

### Requirement: Browser shows file action diagnostics
The browser SHALL provide a `file actions` command that explains the resolved source for open, copy, and reveal actions.

#### Scenario: Show unified action sources
- **WHEN** the user runs `file actions`
- **THEN** the browser SHALL show one diagnostic line for `open`
- **AND** SHALL show one diagnostic line for `copy`
- **AND** SHALL show one diagnostic line for `reveal`
- **AND** SHALL NOT execute any file action

### Requirement: File action failures include source context
The browser SHALL include resolved command source context when a file action cannot run.

#### Scenario: Copy command fails
- **WHEN** `copy path` resolves to a configured command
- **AND** the command fails to launch or returns failure
- **THEN** the user-visible failure message SHALL include the source and command summary

#### Scenario: Reveal command is missing
- **WHEN** `reveal` has no configured command and no platform fallback
- **THEN** the user-visible failure message SHALL include that the source is `missing`

### Requirement: Editor handoff failures include source context
The browser SHALL include resolved command source context when editor handoff cannot run.

#### Scenario: Open command fails
- **WHEN** `open` resolves to a command
- **AND** the command fails to launch
- **THEN** the user-visible failure message SHALL include the source and command summary

#### Scenario: Open command is missing
- **WHEN** no open command can be resolved
- **THEN** the user-visible failure message SHALL include that the source is `missing`

### Requirement: Command palette shows filtered result counts
The browser SHALL show match count feedback when command palette filtering is active.

#### Scenario: Filter has matches
- **WHEN** the command palette filter is `build`
- **THEN** the command palette SHALL show the filter text
- **AND** SHALL show the number of matching executable commands
- **AND** SHALL show the total executable command count

#### Scenario: Filter has no matches
- **WHEN** the command palette filter is `zz-missing`
- **THEN** the command palette SHALL show `0` matching commands
- **AND** SHALL show `No matching commands.`

### Requirement: Command palette ranks stronger matches first
The browser SHALL sort filtered command palette results by match quality while preserving original order for ties.

#### Scenario: Command match outranks description match
- **WHEN** a filter matches one command's command/label and another command's description
- **THEN** the command/label match SHALL appear before the description-only match

### Requirement: Unfiltered command palette order remains stable
The browser SHALL keep the existing palette order when no filter is active.

#### Scenario: No filter
- **WHEN** the command palette has no filter
- **THEN** executable commands SHALL appear in their catalog order

### Requirement: Browser summarizes review notes
The browser SHALL provide a command that lists all current review notes without changing the active review layer.

#### Scenario: Show ordered review notes
- **WHEN** the user runs `notes`
- **AND** review notes exist for changed files in the active review scope
- **THEN** the browser SHALL show a `Review notes:` summary
- **AND** notes for current changed files SHALL be ordered by the current review list order
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Show persisted notes outside current changes
- **WHEN** the user runs `notes`
- **AND** `review_notes` contains paths that are not in the active changed files
- **THEN** the browser SHALL include those notes after current changed-file notes
- **AND** those extra notes SHALL be ordered by path

#### Scenario: Show empty review notes state
- **WHEN** the user runs `notes`
- **AND** no review notes exist
- **THEN** the browser SHALL show a clear empty state

### Requirement: Browser copies review notes summary
The browser SHALL provide a command that copies the current review notes summary to the configured clipboard action.

#### Scenario: Copy ordered review notes
- **WHEN** the user runs `copy notes`
- **AND** review notes exist
- **THEN** the browser SHALL copy the same ordered text that `notes` shows
- **AND** the browser SHALL report how many review notes were copied
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Copy filtered review notes
- **WHEN** the user runs `copy notes lifecycle`
- **AND** review notes match `lifecycle`
- **THEN** the browser SHALL copy the same ordered text that `notes lifecycle` shows
- **AND** the browser SHALL report how many matching review notes were copied
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Copy filtered review notes with no matches
- **WHEN** the user runs `copy notes owner`
- **AND** review notes exist but none match `owner`
- **THEN** the browser SHALL report that there are no matching review notes to copy
- **AND** SHALL NOT launch a clipboard command

#### Scenario: Copy review notes from notes alias
- **WHEN** the user runs `notes copy`
- **THEN** the browser SHALL keep copying the full notes summary

### Requirement: Browser filters review notes by query
The browser SHALL provide a command that filters the review notes summary by path or note text.

#### Scenario: Match note text
- **WHEN** the user runs `notes lifecycle`
- **AND** a review note contains `lifecycle`
- **THEN** the browser SHALL show only matching notes
- **AND** SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Match path text case-insensitively
- **WHEN** the user runs `notes sample`
- **AND** a review note path contains `Sample` with different casing
- **THEN** the browser SHALL include that note

#### Scenario: No filtered matches
- **WHEN** the user runs `notes owner`
- **AND** review notes exist but none match `owner`
- **THEN** the browser SHALL show a clear no-match state

#### Scenario: Empty query keeps existing summary
- **WHEN** the user runs `notes`
- **THEN** the browser SHALL keep showing all review notes

### Requirement: Browser copies prompt handoff
The browser SHALL provide commands that copy prompt-ready Markdown for the current review context to the configured clipboard action.

#### Scenario: Copy current visible scope prompt with review notes
- **WHEN** the user runs `copy prompt`
- **AND** visible changed files have review notes in the current Review Workspace
- **THEN** the copied prompt SHALL include matching review notes for those visible files
- **AND** SHALL NOT include review notes for files outside the copied visible file set
- **AND** the browser SHALL keep the current page, selection, Review Scope, file filter, progress markers, review notes, and task state unchanged

#### Scenario: Copy selected file prompt with review note
- **WHEN** the user runs `copy prompt file`
- **AND** the selected visible changed file has a review note
- **THEN** the copied prompt SHALL include that review note
- **AND** SHALL NOT include review notes for other files

### Requirement: Browser command catalog module owns command surface data
The browser SHALL use a dedicated UI module for command catalog data, executable palette entries, command filtering, and command command-surface line rendering.

#### Scenario: Command catalog exposes grouped commands
- **WHEN** code asks for the browser command catalog
- **THEN** the module SHALL return the existing command groups in their existing order
- **AND** command labels, descriptions, and executable actions SHALL remain unchanged

#### Scenario: Executable palette entries exclude placeholders
- **WHEN** code asks for command palette entries
- **THEN** the module SHALL include executable commands such as `build`, `copy path`, and `copy prompt`
- **AND** SHALL exclude non-executable placeholder entries such as `base REF`, `note TEXT`, and `copy notes QUERY`

#### Scenario: Command palette filtering preserves ranking
- **WHEN** code filters command palette entries
- **THEN** exact and prefix command/label matches SHALL rank before group matches
- **AND** group matches SHALL rank before description-only matches
- **AND** stable catalog order SHALL break ties

#### Scenario: Browser preserves command palette behavior
- **WHEN** the browser renders the command list or command palette
- **THEN** the output SHALL preserve the existing command text, match counts, empty state, selection marker, and clipped-window behavior
- **AND** the browser SHALL keep owning command selection, command filter text, and command scroll state

### Requirement: Browser workspace persistence module owns state file I/O
The browser SHALL use a dedicated UI module for browser workspace persistence file paths, version wrapping, JSON read/write, load validation, and save/restore eligibility decisions.

#### Scenario: Save workspace state through persistence module
- **WHEN** the browser saves default workspace state
- **THEN** the persistence module SHALL write `.git/cr/browse-state.json`
- **AND** SHALL include schema version `1`
- **AND** SHALL preserve the existing workspace state fields
- **AND** SHALL NOT persist task runtime or task history

#### Scenario: Load valid workspace state
- **WHEN** the persistence module loads a valid state file
- **THEN** it SHALL return the persisted state mapping
- **AND** SHALL reject files with invalid JSON, non-object roots, wrong versions, or missing scope objects

#### Scenario: Preserve restore and save eligibility
- **WHEN** a browse session uses explicit staged/all/base/range/untracked/path arguments
- **THEN** default workspace restore SHALL NOT run
- **AND** save-on-exit SHALL NOT write state for explicit path arguments

#### Scenario: Browser delegates persistence without changing behavior
- **WHEN** existing browser wrapper functions are called
- **THEN** they SHALL preserve current behavior
- **AND** their implementation SHALL delegate file I/O and persistence schema handling to the workspace persistence module

### Requirement: Browser Frame module owns screen-region layout
The system SHALL provide a Browser Frame rendering module that owns terminal height measurement, prompt row calculation, main-content height calculation, task-panel height calculation, and task-panel start-row calculation.

#### Scenario: Layout reserves prompt and task panel regions
- **WHEN** a background task is present on a 12-row terminal
- **THEN** the Browser Frame module SHALL reserve the final row for the prompt and place the task panel above it without consuming the main content region entirely

#### Scenario: Layout without task keeps prompt at bottom
- **WHEN** no background task is present on a 12-row terminal
- **THEN** the Browser Frame module SHALL reserve the final row for the prompt and give the remaining rows to main content

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

### Requirement: Browser keeps page rendering orchestration
The browser SHALL continue to own page-specific main content generation, command execution, prompt input flow, and workspace save/restore orchestration while delegating Browser Frame and Task Panel presentation implementation to the frame module.

#### Scenario: Browser wrappers preserve existing behavior
- **WHEN** existing browser helper entry points such as `_screen_layout`, `_task_panel_lines`, `_draw_task_panel_only`, and `_fit_terminal_line` are called
- **THEN** they SHALL return the same observable results through delegation to the Browser Frame module

### Requirement: Save current visible prompt handoff
The browser SHALL support `save prompt [PATH]` to write prompt-ready Markdown for the current visible changed files to a file.

#### Scenario: Save visible scope to default path
- **WHEN** the current browser scope has visible changed files and the user runs `save prompt`
- **THEN** the browser SHALL write the same prompt-ready Markdown used by `copy prompt` to `.cr/handoff/review-prompt.md`
- **AND** the browser SHALL report the saved repo-relative path without changing page, selection, Review Scope, file filter, progress markers, review notes, or task state

#### Scenario: Save visible scope to explicit path
- **WHEN** the current browser scope has visible changed files and the user runs `save prompt tmp/review.md`
- **THEN** the browser SHALL write the prompt-ready Markdown to `tmp/review.md` relative to the repository root

### Requirement: Save selected file prompt handoff
The browser SHALL support `save prompt file [PATH]` to write prompt-ready Markdown for only the selected visible changed file to a file.

#### Scenario: Save selected file to default path
- **WHEN** the current browser scope has a selected visible changed file and the user runs `save prompt file`
- **THEN** the browser SHALL write the same prompt-ready Markdown used by `copy prompt file` to `.cr/handoff/review-prompt-file.md`
- **AND** the generated handoff SHALL include review notes only for the selected file

#### Scenario: Save selected file to explicit path
- **WHEN** the current browser scope has a selected visible changed file and the user runs `save prompt file tmp/file.md`
- **THEN** the browser SHALL write the selected-file prompt-ready Markdown to `tmp/file.md` relative to the repository root

### Requirement: Save prompt handles empty and failed writes
The browser SHALL avoid writing files when there is no matching changed-file content and SHALL surface file write failures as status messages.

#### Scenario: Empty visible scope does not write
- **WHEN** the current browser scope has no visible changed files and the user runs `save prompt`
- **THEN** the browser SHALL not create a handoff file
- **AND** the browser SHALL report that there are no changed files to save

#### Scenario: Missing selected file does not write
- **WHEN** the current browser scope has no visible selected changed file and the user runs `save prompt file`
- **THEN** the browser SHALL not create a handoff file
- **AND** the browser SHALL report that there is no changed file to save

#### Scenario: Write failure is reported
- **WHEN** prompt handoff text is generated but the target file cannot be written
- **THEN** the browser SHALL report a file-save failure message without crashing or changing browser state

### Requirement: Save prompt commands are discoverable
The browser command parser and command catalog SHALL expose save prompt commands alongside existing copy prompt commands.

#### Scenario: Commands parse to stable actions
- **WHEN** `save prompt`, `save prompt PATH`, `save prompt file`, or `save prompt file PATH` is parsed
- **THEN** the parser SHALL return stable save-prompt actions with any explicit path captured as the action value

#### Scenario: Command catalog includes save actions
- **WHEN** the command catalog or palette is shown
- **THEN** it SHALL include `save prompt` and `save prompt file` entries

### Requirement: Page Content Module Ownership

`cr browse` page-specific main content rendering MUST be owned by a dedicated UI module rather than browser session orchestration.

#### Scenario: Browser renders through Page Content

- **GIVEN** an interactive browser state on Scope Home, Commit Picker, Changed Files, or File Detail
- **WHEN** the browser draws the main content area
- **THEN** page-specific text such as scope options, commit rows, changed-file tree rows, empty states, and file detail lines is generated by the Page Content module
- **AND** Browser Frame remains responsible for screen placement and Task Panel presentation
- **AND** browser orchestration remains responsible for input, command execution, workspace startup/exit, and selected-file side effects

### Requirement: Page Content Behavior Preservation

Extracting Page Content MUST preserve existing user-visible browser page behavior.

#### Scenario: Existing pages keep the same visible output

- **GIVEN** the same browser state, CLI args, terminal style, and terminal height as before extraction
- **WHEN** Scope Home, Commit Picker, Changed Files, empty Changed Files, or File Detail content is rendered
- **THEN** prompts, help text, breadcrumbs, changed-file tree styling, progress lines, note markers, commit rows, file detail headers, risk/purpose/symbol lines, hunk lines, and scroll footers remain behaviorally equivalent
- **AND** list, commit, command, and file scroll offsets are still clamped to the visible window

### Requirement: Browser Input Module Ownership

`cr browse` terminal input protocol MUST be owned by a dedicated UI module rather than browser session orchestration.

#### Scenario: Browser reads commands through Browser Input

- **GIVEN** an interactive browser session in raw-key or line mode
- **WHEN** the browser waits for the next command or temporary query
- **THEN** terminal input details such as raw-key detection, command reading, query reading, raw escape parsing, and EOF/interrupt/tick sentinels are provided by the Browser Input module
- **AND** browser orchestration remains responsible for interpreting returned command text, mutating state, restoring the Browser Frame, saving workspace state, and executing commands

### Requirement: Browser Input Behavior Preservation

Extracting Browser Input MUST preserve existing user-visible input behavior.

#### Scenario: Existing input tokens stay stable

- **GIVEN** the same stdin/stdout TTY state, raw-key bytes, line input, EOF, KeyboardInterrupt, and idle timeout as before extraction
- **WHEN** browser input is read
- **THEN** returned command tokens remain behaviorally equivalent, including `__tick__`, `__eof__`, `__interrupt__`, `filter_prompt`, `command_prompt`, arrow navigation, paging, home/end, vim-style movement keys, space, and ordinary character commands
- **AND** normal raw-key reads do not print an extra newline
- **AND** temporary prompt cancellation still lets the browser run loop force a full redraw

### Requirement: Selected File Actions Module Ownership

`cr browse` selected-file action workflow MUST be owned by a dedicated UI module rather than browser command execution.

#### Scenario: Browser executes selected-file workflow through a module

- **GIVEN** a parsed browser action such as open, copy path, copy anchor, reveal, note, copy prompt file, or save prompt file
- **WHEN** the action depends on the current selected changed file or current visible changed-file set
- **THEN** selected-file path/line/note/prompt workflow is performed by the Selected File Actions module
- **AND** BrowserCommandExecutor remains responsible for routing parsed commands and placing returned messages into the browser UI
- **AND** platform subprocess details remain owned by `cr.ui.file_actions`
- **AND** prompt Markdown rendering remains owned by `cr.review.prompt`

### Requirement: Selected File Actions Behavior Preservation

Extracting Selected File Actions MUST preserve existing user-visible behavior.

#### Scenario: Existing selected-file actions keep messages and side effects

- **GIVEN** the same browser state, args, selected file, configured open/copy/reveal commands, review notes, and prompt save path as before extraction
- **WHEN** open, copy path, copy anchor, reveal, note set/clear, copy prompt, copy prompt file, save prompt, or save prompt file is executed
- **THEN** user-facing messages, clipboard/editor/reveal invocation, first-line anchor calculation, review-note filtering, workspace sync, file cache invalidation, prompt save path behavior, and empty-state messages remain behaviorally equivalent
- **AND** raw-key redraw/status behavior remains owned by BrowserCommandExecutor and is unchanged

### Requirement: Browser stages selected file
The browser SHALL provide a selected-file command that stages the current changed file.

#### Scenario: Stage selected file
- **WHEN** the user runs `stage` with a changed file selected in a mutable local scope
- **THEN** the browser SHALL stage that repo-relative path through Git
- **AND** refresh the active Review Scope after the action succeeds
- **AND** show status feedback through the existing browser message/status area

#### Scenario: Stage with no selected file
- **WHEN** the user runs `stage` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without running Git

### Requirement: Browser unstages selected file
The browser SHALL provide a selected-file command that removes the current changed file from the index.

#### Scenario: Unstage selected file
- **WHEN** the user runs `unstage` with a changed file selected in a mutable local scope
- **THEN** the browser SHALL unstage that repo-relative path through Git
- **AND** refresh the active Review Scope after the action succeeds
- **AND** show status feedback through the existing browser message/status area

#### Scenario: Unstage with no selected file
- **WHEN** the user runs `unstage` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without running Git

### Requirement: Index actions preserve read-only review scopes
The browser SHALL NOT mutate Git index state while the active Review Scope is a read-only comparison scope.

#### Scenario: Stage in read-only scope
- **WHEN** the active scope is `base REF`, `range OLD..NEW`, or a selected commit scope
- **AND** the user runs `stage`
- **THEN** the browser SHALL report that index actions are only available for local worktree/index scopes
- **AND** SHALL NOT run Git staging

#### Scenario: Unstage in read-only scope
- **WHEN** the active scope is `base REF`, `range OLD..NEW`, or a selected commit scope
- **AND** the user runs `unstage`
- **THEN** the browser SHALL report that index actions are only available for local worktree/index scopes
- **AND** SHALL NOT run Git unstaging

### Requirement: Index actions use browser command infrastructure
The browser SHALL expose selected-file index actions through the existing parser, command palette, and action executor.

#### Scenario: Command palette lists index actions
- **WHEN** the command palette is rendered
- **THEN** `stage` and `unstage` SHALL appear as executable file commands

### Requirement: Local changes expose source facts
The system SHALL annotate local changed-file facts with their current Git index/worktree source.

#### Scenario: Staged scope source
- **WHEN** changed files are loaded for staged/index review
- **THEN** each returned tracked file change SHALL have source `staged`

#### Scenario: Worktree scope source
- **WHEN** changed files are loaded for unstaged worktree review
- **THEN** each returned tracked file change SHALL have source `unstaged`

#### Scenario: All-local mixed source
- **WHEN** changed files are loaded for all local changes
- **AND** a path has both staged and unstaged changes
- **THEN** that file change SHALL have source `mixed`

#### Scenario: Read-only comparison scope
- **WHEN** changed files are loaded for `base`, `range`, or selected commit comparison
- **THEN** returned file changes SHALL NOT have local source badges

### Requirement: Browser renders change source badges
The browser SHALL show local change source badges in Changed Files rows.

#### Scenario: Changed Files row with source
- **WHEN** a visible changed file has source `staged`, `unstaged`, or `mixed`
- **THEN** the Changed Files row SHALL include that source badge
- **AND** preserve progress, note, status, counts, and tree label rendering

#### Scenario: Changed Files row without source
- **WHEN** a visible changed file has no local source
- **THEN** the Changed Files row SHALL omit the source badge

### Requirement: Browser filters Changed Files by source
The browser SHALL support a source filter inside the current Changed Files view.

#### Scenario: Filter staged files
- **WHEN** the user runs `source staged`
- **THEN** visible changes SHALL include only files whose source is `staged`

#### Scenario: Filter unstaged files
- **WHEN** the user runs `source unstaged`
- **THEN** visible changes SHALL include only files whose source is `unstaged`

#### Scenario: Filter mixed files
- **WHEN** the user runs `source mixed`
- **THEN** visible changes SHALL include only files whose source is `mixed`

#### Scenario: Clear source filter
- **WHEN** the user runs `source all` or `source clear`
- **THEN** the source filter SHALL be cleared

### Requirement: Source filter composes with existing Changed Files filters
The source filter SHALL compose with path filtering and remaining-only filtering.

#### Scenario: Path and source filters combine
- **WHEN** a path filter and source filter are both active
- **THEN** visible changes SHALL match both filters

#### Scenario: Remaining-only and source filters combine
- **WHEN** remaining-only mode and source filter are both active
- **THEN** visible changes SHALL exclude seen paths and match the source filter

### Requirement: Browser displays active source filter
The browser SHALL show active source filter context in Changed Files rendering.

#### Scenario: Active source filter header
- **WHEN** a source filter is active
- **THEN** Changed Files output SHALL show the active source filter

### Requirement: Source filter uses existing command infrastructure
The browser SHALL expose source filtering through the parser, command palette, and action executor.

#### Scenario: Command palette lists source filter commands
- **WHEN** command palette entries are built
- **THEN** source filter commands SHALL be executable entries

### Requirement: Browser displays local source counts
The browser SHALL display a Changed Files source summary when the rendered changes include local source facts.

#### Scenario: Show source summary for local changes
- **WHEN** Changed Files renders visible changes with `FileChange.source` values of `staged`, `unstaged`, or `mixed`
- **THEN** Changed Files output SHALL include counts for the present local source values

#### Scenario: Omit absent source values
- **WHEN** Changed Files renders local changes with only one or two present source values
- **THEN** the source summary SHALL omit zero-count source values

### Requirement: Browser omits source summary without local source facts
The browser SHALL omit the Changed Files source summary when rendered changes do not include local source facts.

#### Scenario: Comparison scope without source facts
- **WHEN** Changed Files renders changes whose `FileChange.source` values are empty
- **THEN** Changed Files output SHALL NOT include a source summary

### Requirement: Scope Home displays count overview
The browser SHALL show overview counts for directly countable Scope Home entries.

#### Scenario: Render changed-file scope counts
- **WHEN** Scope Home renders counts for Worktree, Staged, and All local changes
- **THEN** those entries SHALL include changed-file counts

#### Scenario: Render recent commit count
- **WHEN** Scope Home renders a count for Recent commits
- **THEN** the Recent commits entry SHALL include a commit count

### Requirement: Scope Home count loading is temporary UI state
The browser SHALL load Scope Home counts as temporary UI state without persisting them.

#### Scenario: Open Scope Home loads counts
- **WHEN** the user opens Scope Home
- **THEN** the browser SHALL sample scope counts before rendering the page

#### Scenario: Refresh Scope Home reloads counts
- **WHEN** the user refreshes while Scope Home is active
- **THEN** the browser SHALL reload the Scope Home counts

#### Scenario: Parameterized scopes stay count-free
- **WHEN** Scope Home renders Base ref or Explicit range entries
- **THEN** those entries SHALL remain parameterized command hints without live counts

### Requirement: Recent commit facts include change size
The system SHALL attach changed-file count and line churn totals to recent commit facts.

#### Scenario: Parse recent commit stats
- **WHEN** recent commits are loaded from Git
- **THEN** each returned commit fact SHALL include the number of changed files
- **AND** SHALL include added and deleted line totals when Git reports numeric stats

#### Scenario: Preserve commit identity
- **WHEN** recent commit facts include change size
- **THEN** each commit SHALL still include commit hash, parent hash, authored date, and subject

### Requirement: Commit Picker displays change size
The browser SHALL display each recent commit's change size in Commit Picker rows.

#### Scenario: Render commit row summary
- **WHEN** a Commit Picker row has changed-file count and line churn totals
- **THEN** the row SHALL include the file count and added/deleted totals

#### Scenario: Preserve commit picker navigation
- **WHEN** the user selects a commit with displayed change size
- **THEN** the browser SHALL enter the selected commit Review Scope using the same commit identity as before

### Requirement: Commit Picker filters recent commits
The browser SHALL support filtering loaded recent commits while Commit Picker is active.

#### Scenario: Filter commits from prompt
- **WHEN** the user enters a Commit Picker filter query
- **THEN** Commit Picker SHALL show only commits matching the query
- **AND** SHALL remain on Commit Picker

#### Scenario: Match commit fields
- **WHEN** a query matches a commit hash, authored date, subject, or displayed change summary
- **THEN** that commit SHALL remain visible in the filtered Commit Picker list

#### Scenario: Empty commit filter result
- **WHEN** no loaded recent commits match the query
- **THEN** Commit Picker SHALL show an empty filtered result message

### Requirement: Commit Picker filter is isolated
The Commit Picker filter SHALL be isolated from Changed Files and Command Palette filters.

#### Scenario: Clear active commit filter
- **WHEN** the user clears while Commit Picker is active
- **THEN** the Commit Picker filter SHALL be cleared
- **AND** the Changed Files path filter SHALL be preserved

#### Scenario: Select filtered commit
- **WHEN** the user selects a commit from filtered Commit Picker results
- **THEN** the browser SHALL enter the selected commit Review Scope

### Requirement: Commit Picker rules are module-owned
The browser SHALL keep Commit Picker filtering and filtered selection rules in a
dedicated UI module.

#### Scenario: Filter commits through module interface
- **WHEN** browser state or page rendering needs the visible Commit Picker list
- **THEN** it SHALL call the Commit Picker module
- **AND** it SHALL NOT reimplement commit matching in page rendering

#### Scenario: Select from filtered commits
- **WHEN** the user selects a commit while a Commit Picker filter is active
- **THEN** selection SHALL resolve against the module-owned filtered list

### Requirement: Commit Picker module remains pure
The Commit Picker module SHALL NOT own terminal rendering, command parsing, Git
subprocess calls, or browser frame layout.

#### Scenario: Render filtered commits
- **WHEN** Page Content renders Commit Picker rows
- **THEN** Page Content SHALL own the row text
- **AND** the Commit Picker module SHALL only provide commit filtering and
selection facts

### Requirement: Copy selected file diff snippet
The browser SHALL let users copy a compact review diff snippet for the currently
selected changed file.

#### Scenario: Copy selected file diff
- **WHEN** the user runs `copy diff` with a visible changed file selected
- **THEN** the browser SHALL copy a Markdown snippet for exactly that file
- **AND** the snippet SHALL include the selected file path and diff hunks
- **AND** the browser SHALL preserve page, selection, review scope, filters,
  progress, notes, and task state

#### Scenario: Empty selected file diff copy
- **WHEN** the user runs `copy diff` without a visible changed file
- **THEN** the browser SHALL report that no changed file can be copied
- **AND** it SHALL NOT invoke the copy command

#### Scenario: Copy failure
- **WHEN** the configured copy command fails
- **THEN** the browser SHALL surface the copy failure message

### Requirement: Selected file diff snippet is not prompt handoff
The selected file diff snippet SHALL be rendered as compact review context, not
as the full AI review handoff prompt.

#### Scenario: Render compact file snippet
- **WHEN** selected file diff copy renders snippet text
- **THEN** it SHALL include selected-file review facts such as summary, anchor,
seen state, review note, purpose/focus, risks, and hunks when present
- **AND** it SHALL NOT include full prompt request language

### Requirement: Review Notes rules are module-owned
The browser SHALL keep Review Notes summary, filtering, ordering, and copy
message rules in a dedicated UI module.

#### Scenario: Render review notes through module
- **WHEN** the browser needs `notes` or `notes QUERY` output
- **THEN** it SHALL delegate note ordering, filtering, and empty-state text to
  the Review Notes module

#### Scenario: Copy review notes through module
- **WHEN** the browser needs `copy notes` or `copy notes QUERY`
- **THEN** it SHALL delegate rendered text and copy status messages to the
  Review Notes module

### Requirement: Review Notes behavior remains stable
Extracting the module SHALL NOT change user-visible Review Notes behavior.

#### Scenario: Preserve ordering and filtering
- **WHEN** notes are shown or copied
- **THEN** current changed-file notes SHALL remain ordered by changed-file order
- **AND** persisted extra notes SHALL follow sorted by path
- **AND** filtering SHALL remain case-insensitive over path and note text

#### Scenario: Preserve empty states
- **WHEN** there are no notes or no matching filtered notes
- **THEN** the browser SHALL report the same empty-state messages as before

### Requirement: Save selected file diff snippet
The browser SHALL let users save a compact review diff snippet for the currently
selected changed file.

#### Scenario: Save selected file diff to default path
- **WHEN** the user runs `save diff` with a visible changed file selected
- **THEN** the browser SHALL save a Markdown snippet for exactly that file to
  `.cr/handoff/review-diff.md`
- **AND** the browser SHALL preserve page, selection, review scope, filters,
  progress, notes, and task state

#### Scenario: Save selected file diff to requested path
- **WHEN** the user runs `save diff PATH` with a visible changed file selected
- **THEN** the browser SHALL save the selected file Markdown snippet to `PATH`
- **AND** relative paths SHALL resolve from the repository root

#### Scenario: Empty selected file diff save
- **WHEN** the user runs `save diff` without a visible changed file
- **THEN** the browser SHALL report that no changed file can be saved
- **AND** it SHALL NOT write a file

#### Scenario: Save failure
- **WHEN** the selected file diff snippet cannot be written
- **THEN** the browser SHALL surface the write failure message

### Requirement: Jump to next diff hunk in File Detail
The browser SHALL let users jump to the next rendered diff hunk in the current
File Detail view.

#### Scenario: Next hunk moves file scroll
- **WHEN** the user runs `next hunk` in File Detail and a later hunk exists
- **THEN** the browser SHALL move the File Detail scroll to that hunk
- **AND** it SHALL preserve Review Scope, selected file, filters, progress,
  notes, and task state

#### Scenario: Next hunk at last hunk
- **WHEN** the user runs `next hunk` and no later hunk exists
- **THEN** the browser SHALL keep the current scroll
- **AND** it SHALL report that the user is already at the last hunk

### Requirement: Jump to previous diff hunk in File Detail
The browser SHALL let users jump to the previous rendered diff hunk in the
current File Detail view.

#### Scenario: Previous hunk moves file scroll
- **WHEN** the user runs `prev hunk` in File Detail and an earlier hunk exists
- **THEN** the browser SHALL move the File Detail scroll to that hunk
- **AND** it SHALL preserve Review Scope, selected file, filters, progress,
  notes, and task state

#### Scenario: Previous hunk at first hunk
- **WHEN** the user runs `prev hunk` and no earlier hunk exists
- **THEN** the browser SHALL keep the current scroll
- **AND** it SHALL report that the user is already at the first hunk

### Requirement: Hunk navigation empty states
The browser SHALL surface clear feedback when hunk navigation cannot run.

#### Scenario: No rendered hunks
- **WHEN** the user runs `next hunk` or `prev hunk` in File Detail and the file
  has no rendered diff hunk headers
- **THEN** the browser SHALL keep the current scroll
- **AND** it SHALL report that the current file has no diff hunks

#### Scenario: Hunk navigation outside File Detail
- **WHEN** the user runs `next hunk` or `prev hunk` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

### Requirement: Open current File Detail hunk
The browser SHALL let users open the active File Detail hunk in their editor.

#### Scenario: Open hunk from File Detail
- **WHEN** the user runs `open hunk` in File Detail and the current file has a
  rendered hunk header
- **THEN** the browser SHALL open the selected file at that hunk's new-file
  start line through the configured editor handoff
- **AND** it SHALL preserve Review Scope, selected file, filters, progress,
  notes, and task state

#### Scenario: Open hunk uses first hunk before scrolling
- **WHEN** the user runs `open hunk` while the File Detail scroll is before the
  first rendered hunk header
- **THEN** the browser SHALL open the selected file at the first hunk's new-file
  start line

#### Scenario: No rendered hunks
- **WHEN** the user runs `open hunk` in File Detail and no rendered hunk header
  exists
- **THEN** the browser SHALL keep the current page and report that the current
  file has no diff hunks

#### Scenario: Open hunk outside File Detail
- **WHEN** the user runs `open hunk` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

#### Scenario: Editor handoff failure
- **WHEN** the configured editor handoff fails
- **THEN** the browser SHALL surface the editor handoff failure message

### Requirement: Copy current File Detail hunk
The browser SHALL let users copy the active File Detail hunk as compact review
context.

#### Scenario: Copy hunk from File Detail
- **WHEN** the user runs `copy hunk` in File Detail and the current file has a
  rendered hunk header
- **THEN** the browser SHALL copy Markdown containing the selected file path,
  the active hunk anchor, and the active rendered hunk block
- **AND** it SHALL preserve Review Scope, selected file, filters, progress,
  notes, and task state

#### Scenario: Copy hunk uses first hunk before scrolling
- **WHEN** the user runs `copy hunk` while the File Detail scroll is before the
  first rendered hunk header
- **THEN** the browser SHALL copy the first hunk block

#### Scenario: No rendered hunks
- **WHEN** the user runs `copy hunk` in File Detail and no rendered hunk header
  exists
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that the current file has no diff hunks
- **AND** it SHALL NOT invoke the copy command

#### Scenario: Copy hunk outside File Detail
- **WHEN** the user runs `copy hunk` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

#### Scenario: Clipboard failure
- **WHEN** the configured copy command fails
- **THEN** the browser SHALL surface the copy failure message

### Requirement: File Detail hunk workflows are selected-file actions
The browser SHALL route selected File Detail hunk open/copy workflows through
the selected-file action module while preserving current behavior.

#### Scenario: Open selected hunk through selected-file action
- **WHEN** the browser opens the active File Detail hunk
- **THEN** the selected-file action module SHALL resolve the hunk line from the
  rendered File Detail lines
- **AND** it SHALL invoke the configured editor action for that file and line
- **AND** it SHALL return the same success and failure messages as before

#### Scenario: Copy selected hunk through selected-file action
- **WHEN** the browser copies the active File Detail hunk
- **THEN** the selected-file action module SHALL resolve the active rendered
  hunk block from the rendered File Detail lines
- **AND** it SHALL copy the same Markdown hunk text as before
- **AND** it SHALL return the same success and failure messages as before

#### Scenario: Browser keeps page ownership
- **WHEN** `open hunk` or `copy hunk` is executed outside File Detail or without
  a visible selected file
- **THEN** the browser SHALL keep those page/selection checks in browser command
  execution
- **AND** it SHALL NOT ask the selected-file action module to load browser
  state or render file content

### Requirement: Preserve File Detail on ordinary refresh
The browser SHALL keep users in File Detail after ordinary refresh when the
selected file is still visible in the refreshed Review Scope.

#### Scenario: Selected file survives refresh
- **WHEN** the user runs `refresh` from File Detail
- **AND** the selected path is still present after reloading changed files and
  applying the active filters
- **THEN** the browser SHALL remain in File Detail
- **AND** it SHALL keep that path selected
- **AND** it SHALL clamp the previous file scroll to the refreshed File Detail
  height
- **AND** it SHALL reset page back/forward history for the reloaded scope

#### Scenario: Selected file disappears on refresh
- **WHEN** the user runs `refresh` from File Detail
- **AND** the selected path is no longer visible after reloading changed files
- **THEN** the browser SHALL show Changed Files
- **AND** it SHALL reset File Detail scroll
- **AND** it SHALL report that the current file is no longer changed

#### Scenario: Index-action refresh is unchanged
- **WHEN** a successful `stage` or `unstage` action refreshes the Review Scope
- **THEN** the browser SHALL continue to show Changed Files after the action

### Requirement: Find rendered text in File Detail
The browser SHALL let users jump to rendered text inside the current File
Detail page.

#### Scenario: Find matching rendered text
- **WHEN** the user runs `find TEXT` in File Detail
- **AND** a rendered File Detail body line contains `TEXT` case-insensitively
- **THEN** the browser SHALL set File Detail scroll to the first matching body
  line
- **AND** it SHALL keep the current Review Scope, selected file, notes,
  progress, and task state

#### Scenario: No matching rendered text
- **WHEN** the user runs `find TEXT` in File Detail
- **AND** no rendered body line contains `TEXT`
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that no match was found

#### Scenario: Empty query
- **WHEN** the user runs `find` or `find   `
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that a search query is required

#### Scenario: Find outside File Detail
- **WHEN** the user runs `find TEXT` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

### Requirement: Repeat File Detail text search
The browser SHALL let users repeat the most recent File Detail text search
within the current rendered file.

#### Scenario: Move to next match
- **WHEN** the user has run `find TEXT` in File Detail
- **AND** the user runs `next match`
- **THEN** the browser SHALL jump to the next rendered body line containing
  `TEXT` case-insensitively
- **AND** it SHALL wrap to the first match when already at or after the last
  match

#### Scenario: Move to previous match
- **WHEN** the user has run `find TEXT` in File Detail
- **AND** the user runs `prev match`
- **THEN** the browser SHALL jump to the previous rendered body line containing
  `TEXT` case-insensitively
- **AND** it SHALL wrap to the last match when already at or before the first
  match

#### Scenario: No prior find query
- **WHEN** the user runs `next match` or `prev match` before `find TEXT`
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that `find TEXT` must run first

#### Scenario: Stored query no longer matches
- **WHEN** the user runs `next match` or `prev match`
- **AND** the stored query no longer matches the current rendered File Detail
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that no match was found

### Requirement: File Detail current line actions
The browser SHALL let users open or copy the new-file anchor for the current rendered File Detail line when that line has a new-file line number.

#### Scenario: Open current rendered line
- **WHEN** the user is in File Detail on a rendered hunk header, context line, or added line with a new-file line number
- **AND** the user runs `open line`
- **THEN** the browser SHALL open the selected file at that new-file line number through the configured editor action
- **AND** it SHALL keep the current Review Scope, selected file, filters, notes, progress, task state, page, and file scroll

#### Scenario: Copy current rendered line anchor
- **WHEN** the user is in File Detail on a rendered hunk header, context line, or added line with a new-file line number
- **AND** the user runs `copy line`
- **THEN** the browser SHALL copy `path:line` for the selected file and current new-file line number through the configured copy action
- **AND** it SHALL keep the current Review Scope, selected file, filters, notes, progress, task state, page, and file scroll

#### Scenario: Current line has no new-file line number
- **WHEN** the user is in File Detail on a deleted line, file header, note, purpose, risk, or other rendered line without a new-file line number
- **AND** the user runs `open line` or `copy line`
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that no current new-file line is available

#### Scenario: Line action outside File Detail
- **WHEN** the user runs `open line` or `copy line` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

### Requirement: File Detail changed-line navigation
The browser SHALL let users jump between actual added/deleted rows in the current rendered File Detail.

#### Scenario: Move to next changed row
- **WHEN** the user is in File Detail
- **AND** the current rendered file contains at least one added or deleted row
- **AND** the user runs `next change`
- **THEN** the browser SHALL move File Detail scroll to the next added/deleted row after the current scroll
- **AND** it SHALL wrap to the first added/deleted row when already at or after the last changed row
- **AND** it SHALL keep the current Review Scope, selected file, filters, notes, progress, task state, and page

#### Scenario: Move to previous changed row
- **WHEN** the user is in File Detail
- **AND** the current rendered file contains at least one added or deleted row
- **AND** the user runs `prev change`
- **THEN** the browser SHALL move File Detail scroll to the previous added/deleted row before the current scroll
- **AND** it SHALL wrap to the last added/deleted row when already at or before the first changed row
- **AND** it SHALL keep the current Review Scope, selected file, filters, notes, progress, task state, and page

#### Scenario: No changed rows
- **WHEN** the user is in File Detail
- **AND** the current rendered file has no added or deleted rows
- **AND** the user runs `next change` or `prev change`
- **THEN** the browser SHALL keep the current scroll
- **AND** it SHALL report that there are no changed rows in the current file

#### Scenario: Outside File Detail
- **WHEN** the user runs `next change` or `prev change` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

### Requirement: File Detail current change copy
The browser SHALL let users copy compact review context for the current actual changed row in File Detail.

#### Scenario: Copy current added row
- **WHEN** the user is in File Detail on a rendered added row with a new-file line number
- **AND** the user runs `copy change`
- **THEN** the browser SHALL copy a compact review snippet containing the selected path, `path:new_line` anchor, change kind, and cleaned rendered row text
- **AND** it SHALL keep the current Review Scope, selected file, filters, notes, progress, task state, page, and file scroll

#### Scenario: Copy current deleted row
- **WHEN** the user is in File Detail on a rendered deleted row with an old-file line number
- **AND** the user runs `copy change`
- **THEN** the browser SHALL copy a compact review snippet containing the selected path, old line number, change kind, and cleaned rendered row text
- **AND** it SHALL NOT invent a new-file anchor for the deleted row
- **AND** it SHALL keep the current Review Scope, selected file, filters, notes, progress, task state, page, and file scroll

#### Scenario: Current row is not an actual change
- **WHEN** the user is in File Detail on a context row, hunk header, file header, note, purpose, risk, or other rendered row that is not an added/deleted row
- **AND** the user runs `copy change`
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that no current changed row is available

#### Scenario: Copy change outside File Detail
- **WHEN** the user runs `copy change` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

### Requirement: File Detail current change notes
The browser SHALL let users append a review note for the current actual changed row in File Detail.

#### Scenario: Note current added row
- **WHEN** the user is in File Detail on a rendered added row with a new-file line number
- **AND** the user runs `note change TEXT`
- **THEN** the browser SHALL append `line N: TEXT` to the selected file's review note
- **AND** it SHALL keep the current Review Scope, selected file, filters, progress, task state, page, and file scroll

#### Scenario: Note current deleted row
- **WHEN** the user is in File Detail on a rendered deleted row with an old-file line number
- **AND** the user runs `note change TEXT`
- **THEN** the browser SHALL append `old line N: TEXT` to the selected file's review note
- **AND** it SHALL NOT invent a new-file line number for the deleted row

#### Scenario: Preserve existing file note
- **WHEN** the selected file already has a review note
- **AND** the user runs `note change TEXT` on a current changed row
- **THEN** the browser SHALL append the change note to the existing file note without deleting the existing text

#### Scenario: Current row is not an actual change
- **WHEN** the user is in File Detail on a context row, hunk header, file header, note, purpose, risk, or other rendered row that is not an added/deleted row
- **AND** the user runs `note change TEXT`
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that no current changed row is available

#### Scenario: Missing change note text
- **WHEN** the user runs `note change` without non-empty note text
- **THEN** the browser SHALL keep existing review notes unchanged
- **AND** it SHALL treat `note change` as a normal file-level note for compatibility

#### Scenario: Change note outside File Detail
- **WHEN** the user runs `note change TEXT` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first

### Requirement: Done next review flow
The browser SHALL let users mark the selected visible changed file as seen and advance to the next visible changed file with one command.

#### Scenario: Done next from Changed Files
- **WHEN** the user is on Changed Files with multiple visible changed files
- **AND** the user runs `done next`
- **THEN** the browser SHALL mark the current selected file as seen
- **AND** it SHALL select the next visible changed file
- **AND** it SHALL remain on Changed Files

#### Scenario: Done next from File Detail
- **WHEN** the user is in File Detail with multiple visible changed files
- **AND** the user runs `done next`
- **THEN** the browser SHALL mark the current file as seen
- **AND** it SHALL open the next visible file detail
- **AND** it SHALL reset File Detail scroll for the next file

#### Scenario: Done next with remaining filter
- **WHEN** remaining-only mode is active and the selected file is visible
- **AND** the user runs `done next`
- **THEN** the browser SHALL mark the current file as seen
- **AND** it SHALL select the file now occupying the same visible index after the seen file is filtered out
- **AND** it SHALL NOT skip that next remaining file

#### Scenario: Done next on last visible file
- **WHEN** the selected file is the last visible changed file
- **AND** the user runs `done next`
- **THEN** the browser SHALL mark the current file as seen
- **AND** it SHALL keep a valid selection if any visible file remains
- **AND** it SHALL report that there is no next file when no later visible file exists

#### Scenario: Done next without visible files
- **WHEN** there are no visible changed files
- **AND** the user runs `done next`
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that there is no changed file to mark seen

### Requirement: 页面展示上下文动作条
系统 SHALL 在 raw-key `cr browse` frame 中展示一行与当前页面相关的高频动作提示。

#### Scenario: Changed Files 动作条
- **WHEN** 用户位于 Changed Files 页面
- **THEN** frame SHALL 展示包含打开文件、过滤、标记已看、done-next、任务和命令面板入口的动作条

#### Scenario: File Detail 动作条
- **WHEN** 用户位于 File Detail 页面
- **THEN** frame SHALL 展示包含 hunk/change 导航、查找、打开/复制当前位置、done-next 和返回文件列表的动作条

#### Scenario: Scope Home 动作条
- **WHEN** 用户位于 Scope Home 页面
- **THEN** frame SHALL 展示包含选择 scope、返回、recent commits、base/range 命令和命令面板入口的动作条

#### Scenario: Commit Picker 动作条
- **WHEN** 用户位于 Commit Picker 页面
- **THEN** frame SHALL 展示包含选择 commit、过滤 commit、清除过滤、返回和命令面板入口的动作条

#### Scenario: Command Palette 动作条
- **WHEN** 用户位于 Command Palette 页面
- **THEN** frame SHALL 展示包含执行命令、搜索命令、清除搜索和返回的动作条

### Requirement: 动作条保持 frame 布局稳定
系统 MUST 将上下文动作条作为 main content 的一部分渲染，并保持 prompt 与 Task Panel 区域稳定。

#### Scenario: Task Panel 运行时
- **WHEN** 后台 task 正在运行并触发 raw-key full redraw
- **THEN** frame SHALL 仍保留 Task Panel 区域并在主内容区域内展示动作条

#### Scenario: 终端宽度不足
- **WHEN** 动作条文本超过终端宽度
- **THEN** frame SHALL 截断动作条单行文本而不是让它换行破坏布局

### Requirement: 动作条不改变命令行为
系统 MUST 只展示已有命令提示，不改变命令解析、workspace state 或持久化 schema。

#### Scenario: Existing command parsing
- **WHEN** 用户输入已有命令或快捷键
- **THEN** command parser SHALL 返回与引入动作条之前相同的 BrowserCommandAction

#### Scenario: Workspace persistence
- **WHEN** 浏览器保存 workspace state
- **THEN** persisted data SHALL NOT include contextual action bar state

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

### Requirement: 任务输出 handoff 不改变任务运行时
系统 MUST 将 task output handoff 作为命令副作用处理，不改变 task lifecycle、task history 或 workspace persistence。

#### Scenario: Command parsing remains explicit
- **WHEN** 用户输入 `copy task` 或 `save task`
- **THEN** command parser SHALL 返回专用 task output handoff action

#### Scenario: Workspace persistence unchanged
- **WHEN** 浏览器保存 workspace state
- **THEN** persisted data SHALL NOT include task output handoff content

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

### Requirement: File Detail find behavior remains stable

Extracting shared rendered-text search SHALL preserve File Detail find behavior.

#### Scenario: File Detail find still searches rendered detail text

- **GIVEN** File Detail is visible
- **WHEN** the user runs `find TEXT`, `next match`, or `prev match`
- **THEN** the browser SHALL keep the same File Detail messages, scroll behavior, and `file_find_text` behavior as before

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

### Requirement: Browser shows Task Problems page

The browser SHALL provide a Task Problems page for the current task output.

#### Scenario: Open Task Problems page

- **WHEN** the user runs `problems` or `task problems`
- **THEN** the browser SHALL enter Task Problems page
- **AND** the page SHALL participate in browser back/forward page history
- **AND** selection and scroll SHALL reset when the page opens

#### Scenario: Render Task Problems

- **GIVEN** current task output has extracted problems
- **WHEN** Task Problems page renders
- **THEN** it SHALL show each problem's path, line, optional column, and source output summary

#### Scenario: Render empty state

- **GIVEN** no current task exists or no problem anchors are extracted
- **WHEN** Task Problems page renders
- **THEN** it SHALL show an empty Task Problems state

### Requirement: Browser opens selected task problem

Task Problems page SHALL let users open the selected problem in their editor.

#### Scenario: Open selected problem

- **GIVEN** Task Problems page is visible with at least one problem selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL open the problem path at its line through the existing editor open action
- **AND** it SHALL keep Task Problems page visible

#### Scenario: Navigate task problems

- **GIVEN** Task Problems page is visible with multiple problems
- **WHEN** the user presses movement, paging, home, or end keys
- **THEN** the browser SHALL update problem selection and scroll within valid bounds

### Requirement: Browser copies selected task problem

The browser SHALL copy the selected Task Problems entry.

#### Scenario: Copy selected problem

- **GIVEN** Task Problems Page is visible with at least one problem selected
- **WHEN** the user runs `copy problem`
- **THEN** the browser SHALL copy text containing the selected problem location and output summary
- **AND** the browser SHALL keep the current page, selection, scroll, Review Scope, and task state unchanged

#### Scenario: Copy selected problem empty state

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `copy problem`
- **THEN** the browser SHALL report that no task problem can be copied
- **AND** it SHALL NOT launch the clipboard command

### Requirement: Browser copies all task problems

The browser SHALL copy every current Task Problems entry.

#### Scenario: Copy all problems

- **GIVEN** current task output has extracted problems
- **WHEN** the user runs `copy problems`
- **THEN** the browser SHALL copy a compact list containing every problem location and output summary in current output order

#### Scenario: Copy all problems empty state

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `copy problems`
- **THEN** the browser SHALL report that no task problems can be copied
- **AND** it SHALL NOT launch the clipboard command

### Requirement: Browser opens source preview from task problem

The browser SHALL provide a read-only Source File Page for the selected Task Problems entry.

#### Scenario: View selected problem source

- **GIVEN** Task Problems Page is visible with a selected problem
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL enter Source File Page for that problem's repo-local path
- **AND** it SHALL mark the problem line
- **AND** the previous Task Problems Page SHALL be reachable through browser back history

#### Scenario: Preserve external editor enter behavior

- **GIVEN** Task Problems Page is visible
- **WHEN** the user presses Enter
- **THEN** the browser SHALL continue to open the selected problem through the existing external editor action

#### Scenario: No selected problem

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL report that no task problem can be viewed
- **AND** it SHALL keep the current page visible

### Requirement: Browser renders source file page

Source File Page SHALL render source text with line numbers.

#### Scenario: Render target line

- **GIVEN** Source File Page has a readable repo-local text file and target line
- **WHEN** the page renders
- **THEN** it SHALL show the repo-relative path
- **AND** it SHALL show line-numbered source rows
- **AND** it SHALL mark the target line

#### Scenario: Scroll source file

- **GIVEN** Source File Page is visible
- **WHEN** the user presses movement, paging, home, or end keys
- **THEN** the browser SHALL update source scroll within valid bounds

#### Scenario: Render unreadable source

- **GIVEN** Source File Page references a missing or unreadable file
- **WHEN** the page renders
- **THEN** it SHALL show a clear source-file empty/error state

### Requirement: Browser searches Source File Page

The browser SHALL search text within the current Source File Page.

#### Scenario: Find source text

- **GIVEN** Source File Page is visible with a readable source file
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL search source lines case-insensitively
- **AND** it SHALL move the Source File Page target line to the first matching source line
- **AND** it SHALL keep Review Scope, task state, and page history unchanged

#### Scenario: Missing source text

- **GIVEN** Source File Page is visible with a readable source file
- **WHEN** the user runs `find TEXT` with no matches
- **THEN** the browser SHALL report no matches
- **AND** it SHALL keep the current source target line and scroll unchanged

### Requirement: Browser repeats Source File Page search

The browser SHALL repeat Source File Page searches using page-local query state.

#### Scenario: Next source match

- **GIVEN** Source File Page has a previous non-empty source find query
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL move to the next matching source line with wraparound

#### Scenario: Previous source match

- **GIVEN** Source File Page has a previous non-empty source find query
- **WHEN** the user runs `prev match`
- **THEN** the browser SHALL move to the previous matching source line with wraparound

#### Scenario: No source query

- **GIVEN** Source File Page has no previous source find query
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL ask the user to enter text to find

### Requirement: Browser handles unreadable source find

The browser SHALL handle find on unreadable Source File Page state.

#### Scenario: Find unreadable source

- **GIVEN** Source File Page references a missing or unreadable file
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL report the source-file error without crashing

### Requirement: Browser copies Source File Page line anchors

The browser SHALL copy the current Source File Page target line as a repo-relative `path:line` anchor.

#### Scenario: Copy target source line

- **GIVEN** Source File Page is visible for `src/Foo.ets`
- **AND** its target line is `20`
- **WHEN** the user runs `copy line`
- **THEN** the browser SHALL copy `src/Foo.ets:20`
- **AND** it SHALL stay on Source File Page
- **AND** it SHALL preserve the source scroll and target line.

#### Scenario: Empty source state

- **GIVEN** Source File Page is visible without a source path
- **WHEN** the user runs `copy line`
- **THEN** the browser SHALL report that there is no source file line to copy
- **AND** it SHALL not call the clipboard command.

### Requirement: Browser advertises Source File Page copy line

The browser SHALL expose the Source File Page copy-line action in its contextual action bar.

#### Scenario: Source File Page action bar

- **GIVEN** Source File Page is visible
- **WHEN** the browser renders the contextual action bar
- **THEN** the bar SHALL include `copy line`.

### Requirement: Browser enriches task problems with diagnostics facts

The browser SHALL enrich extracted task problems with optional severity, code, and message facts when common task-output text contains them.

#### Scenario: Extract severity code and message after anchor

- **GIVEN** current task output contains `src/Foo.ets:12:3 error TS2322: bad call`
- **AND** `src/Foo.ets` exists inside the repo
- **WHEN** task problems are extracted
- **THEN** the extracted problem SHALL have severity `error`
- **AND** code `TS2322`
- **AND** message `bad call`.

#### Scenario: Preserve unknown diagnostics

- **GIVEN** current task output contains a repo-local `path:line[:column]` anchor but no recognized severity or code
- **WHEN** task problems are extracted
- **THEN** the problem SHALL still be returned
- **AND** its diagnostic facts SHALL be empty
- **AND** its raw summary SHALL be preserved.

### Requirement: Browser surfaces diagnostics facts in Problems UI and handoff

The browser SHALL surface extracted diagnostics facts in the Problems page and copy handoff text.

#### Scenario: Render compact diagnostic label

- **GIVEN** Task Problems page has a problem with severity `error` and code `TS2322`
- **WHEN** the page renders rows
- **THEN** the row SHALL include a compact `ERROR TS2322` label.

#### Scenario: Copy diagnostic facts

- **GIVEN** a task problem has severity, code, and message
- **WHEN** the user copies that problem
- **THEN** the copied handoff text SHALL include the location plus severity, code, and message facts.

### Requirement: Browser filters Task Problems by severity

The browser SHALL filter current Task Problems by extracted severity without reordering them.

#### Scenario: Show error problems only

- **GIVEN** current task output has error and warning problems
- **WHEN** the user runs `problems errors`
- **THEN** the browser SHALL enter Task Problems page
- **AND** it SHALL show only problems whose severity is `error`
- **AND** it SHALL preserve task-output order among visible error problems.

#### Scenario: Clear severity filter

- **GIVEN** Task Problems page is filtered to warnings
- **WHEN** the user runs `problems all`
- **THEN** the browser SHALL show all current task problems.

### Requirement: Browser applies the visible problem filter to actions

The browser SHALL apply the active severity filter to selection, open, source preview, and copy actions.

#### Scenario: Copy visible filtered problems

- **GIVEN** Task Problems page is filtered to errors
- **WHEN** the user runs `copy problems`
- **THEN** the copied handoff SHALL include only visible error problems.

#### Scenario: Empty filtered state

- **GIVEN** current task output has problems but none match the active severity filter
- **WHEN** Task Problems page renders
- **THEN** it SHALL show a filter-specific empty state.

### Requirement: Browser shows Task Problems severity counts

The browser SHALL show compact severity counts for the currently visible Task Problems list.

#### Scenario: Render mixed severity counts

- **GIVEN** Task Problems page has visible errors, warnings, and unknown-severity problems
- **WHEN** the page renders
- **THEN** the header SHALL include counts for each visible severity bucket
- **AND** unknown-severity problems SHALL be counted as `unknown`.

#### Scenario: Filtered counts are visible counts

- **GIVEN** Task Problems page is filtered to errors
- **WHEN** the page renders
- **THEN** the header SHALL show the visible error count
- **AND** it SHALL not imply hidden warning or info totals.

### Requirement: Browser copies Source File Page source context

The browser SHALL copy a compact source context snippet for the current Source File Page target line.

#### Scenario: Copy source context

- **GIVEN** Source File Page is visible for `src/Foo.ets`
- **AND** its target line is `20`
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL copy Markdown headed by `src/Foo.ets:20`
- **AND** the copied code block SHALL include nearby source lines with line numbers
- **AND** the target line SHALL be marked.

#### Scenario: Empty source state

- **GIVEN** Source File Page is visible without a source path
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL report that there is no source file to copy
- **AND** it SHALL not call the clipboard command.

### Requirement: Browser advertises source context copy

The browser SHALL expose `copy source` in command help and Source File Page actions.

#### Scenario: Source File Page action bar

- **GIVEN** Source File Page is visible
- **WHEN** the contextual action bar renders
- **THEN** it SHALL include `copy source`.

### Requirement: Browser optionally sorts Task Problems by severity

The browser SHALL support an explicit severity sort mode for current Task Problems while keeping output order as the default.

#### Scenario: Sort by severity

- **GIVEN** Task Problems include warnings, errors, notes, and unknown-severity anchors
- **WHEN** the user runs `problems sort severity`
- **THEN** the browser SHALL show errors before warnings, info, notes, and unknown anchors
- **AND** it SHALL preserve task-output order within each severity bucket.

#### Scenario: Restore output order

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the user runs `problems sort output`
- **THEN** the browser SHALL show problems in task-output order.

### Requirement: Browser applies sort mode to visible problem actions

The browser SHALL apply the active sort mode to selection, open, source preview, and copy actions.

#### Scenario: Copy sorted visible problems

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the user runs `copy problems`
- **THEN** the copied handoff SHALL follow the sorted visible order.

#### Scenario: Header shows active sort

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the page renders
- **THEN** the header SHALL show that severity sort is active.

### Requirement: Source File Page copies configurable source context

The browser SHALL let users configure how many source lines around the current Source File Page target line are included by `copy source`.

#### Scenario: Default context remains unchanged

- **GIVEN** the user has not changed Source File Page context
- **WHEN** the user runs `copy source`
- **THEN** the copied snippet SHALL include up to three lines before and after the target line.

#### Scenario: User sets source context radius

- **GIVEN** the user is on Source File Page
- **WHEN** the user runs `source context 1`
- **THEN** future `copy source` output SHALL include up to one line before and after the target line.

#### Scenario: Source context is visible

- **GIVEN** Source File Page is rendered
- **WHEN** the source context radius is active
- **THEN** the page SHALL display the current context radius.

### Requirement: Source context radius is page-local browser state

The browser SHALL keep Source File Page context radius in page-local browser state.

#### Scenario: Page history restores source context

- **GIVEN** Source File Page has source context radius 8
- **WHEN** the user navigates away and then returns through page history
- **THEN** Source File Page SHALL restore source context radius 8.

#### Scenario: Opening a new source file resets context

- **GIVEN** Source File Page has source context radius 8
- **WHEN** the browser opens a different Source File Page from Task Problems
- **THEN** the new Source File Page SHALL use the default radius.

### Requirement: Browser copies selected problem context

The browser SHALL copy a focused Markdown context package for the currently selected task problem.

#### Scenario: Copy context from Task Problems

- **GIVEN** Task Problems has a selected problem whose source file can be read
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include the selected problem facts
- **AND** it SHALL include source context around the problem line
- **AND** it SHALL include same-file diff context when the file is changed in the current Review Scope.

#### Scenario: Copy context without matching diff

- **GIVEN** Task Problems has a selected problem whose file is not changed in the current Review Scope
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include problem and source context
- **AND** it SHALL state that there is no diff in the current review scope.

### Requirement: Browser copies source page context

The browser SHALL copy a focused Markdown context package from Source File Page.

#### Scenario: Copy context from Source File Page

- **GIVEN** Source File Page is open on a repo-local source file
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include the source target anchor
- **AND** it SHALL include source context using the active source context radius
- **AND** it SHALL include same-file diff context when available.

### Requirement: Problem context command is surfaced in TUI commands

The browser SHALL expose `copy problem context` through command parsing, command catalog, and contextual action bars for Task Problems and Source File Page.

#### Scenario: Command is visible

- **GIVEN** the user opens command help or a relevant page action bar
- **WHEN** the browser renders commands
- **THEN** `copy problem context` SHALL be discoverable.

### Requirement: Browser filters Task Problems by text

The browser SHALL support a page-local text filter over current Task Problems.

#### Scenario: Filter by query

- **GIVEN** Task Problems include multiple paths and messages
- **WHEN** the user runs `problems find Foo`
- **THEN** the browser SHALL show only problems whose path, location, summary, severity, code, or message contains `Foo` case-insensitively.

#### Scenario: Clear query

- **GIVEN** Task Problems has an active text query
- **WHEN** the user runs `problems clear find`
- **THEN** the browser SHALL clear the query and show problems using the remaining filters and sort mode.

### Requirement: Text filter composes with existing Task Problems view state

The browser SHALL apply the text query after severity filtering and before sorting.

#### Scenario: Actions use queried visible list

- **GIVEN** Task Problems has an active text query
- **WHEN** the user runs `copy problem`, `copy problems`, `view problem`, or opens a problem
- **THEN** the action SHALL use the queried visible list.

#### Scenario: Header shows query

- **GIVEN** Task Problems has an active text query
- **WHEN** the page renders
- **THEN** the header SHALL show the active query.

#### Scenario: Page history restores query

- **GIVEN** Task Problems has an active text query
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active query SHALL be restored.

### Requirement: Source File Page selects a source range

The browser SHALL support a page-local line range selection in Source File Page.

#### Scenario: Select range

- **GIVEN** Source File Page is open for a repo-local source file
- **WHEN** the user runs `source select 4 8`
- **THEN** the page SHALL record the selected range `4-8`
- **AND** render the active selection in the Source File Page header and rows.

#### Scenario: Normalize reversed range

- **GIVEN** Source File Page is open
- **WHEN** the user runs `source select 8 4`
- **THEN** the page SHALL record the selected range `4-8`.

#### Scenario: Clear range

- **GIVEN** Source File Page has an active selected range
- **WHEN** the user runs `source clear selection`
- **THEN** the page SHALL clear the selected range.

### Requirement: Source range composes with source copy

The browser SHALL make `copy source` copy the active selected source range when
a Source File Page selection exists.

#### Scenario: Copy selected range

- **GIVEN** Source File Page has selected range `4-8`
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL include only source lines 4 through 8
- **AND** report that the selected source range was copied.

#### Scenario: Copy source context without selection

- **GIVEN** Source File Page has no selected range
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL keep the existing context-radius copy behavior.

### Requirement: Source range follows source page lifecycle

The browser SHALL treat range selection as Source File Page local state.

#### Scenario: New source file clears range

- **GIVEN** Source File Page has an active selected range
- **WHEN** another Source File Page is opened
- **THEN** the active selected range SHALL be cleared.

#### Scenario: Page history restores range

- **GIVEN** Source File Page has an active selected range
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active selected range SHALL be restored.

### Requirement: Browser saves focused problem context

The browser SHALL support saving the same focused Problem Context Markdown used
by `copy problem context`.

#### Scenario: Save selected task problem context

- **GIVEN** Task Problems has a selected problem with readable source
- **WHEN** the user runs `save problem context tmp/problem.md`
- **THEN** the browser SHALL write focused problem context Markdown to
  `tmp/problem.md`
- **AND** report the saved path.

#### Scenario: Save source page context

- **GIVEN** Source File Page is open for a readable source file
- **WHEN** the user runs `save problem context`
- **THEN** the browser SHALL write focused source/diff context to
  `.cr/handoff/problem-context.md`.

#### Scenario: No context available

- **GIVEN** neither Task Problems nor Source File Page has an active context
- **WHEN** the user runs `save problem context`
- **THEN** the browser SHALL report that there is no problem context to save.

### Requirement: Problem context save handles write failures

The browser SHALL report file-write failures without changing current page,
selection, task state, or review scope.

#### Scenario: Destination cannot be written

- **GIVEN** Problem Context Markdown can be generated
- **WHEN** saving to the requested destination fails
- **THEN** the browser SHALL report the destination path and the write error.

### Requirement: Browser groups Task Problems by file

The browser SHALL support page-local file grouping for current Task Problems.

#### Scenario: Enable file grouping

- **GIVEN** Task Problems has visible problems from multiple files
- **WHEN** the user runs `problems group file`
- **THEN** the Task Problems page SHALL render file headers before each file's
  problem rows
- **AND** the page header SHALL show that grouping is active.

#### Scenario: Disable grouping

- **GIVEN** Task Problems is grouped by file
- **WHEN** the user runs `problems group none`
- **THEN** the Task Problems page SHALL render the flat problem list.

### Requirement: Grouping composes with visible problem actions

Task Problems grouping SHALL NOT change the visible problem list used by
selection and problem actions.

#### Scenario: Actions use visible problem list

- **GIVEN** Task Problems has grouping enabled
- **WHEN** the user opens, views, copies, or saves context for a selected problem
- **THEN** the action SHALL use the same filtered, queried, and sorted visible
  `TaskProblem` list as flat mode.

#### Scenario: Page history restores grouping

- **GIVEN** Task Problems has grouping enabled
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active grouping mode SHALL be restored.

### Requirement: Page-specific Chinese help
The interactive browser SHALL provide a Help page that explains the currently
active page in Chinese.

#### Scenario: Help opens for the current page
- **GIVEN** the browser is on Task Problems
- **WHEN** the user runs `help`
- **THEN** the browser shows the Help page
- **AND** the Help page describes Task Problems commands in Chinese

#### Scenario: Help preserves navigation
- **GIVEN** the browser opens Help from File Detail
- **WHEN** the user goes back
- **THEN** the browser returns to File Detail with its page state preserved

### Requirement: Chinese visible help surfaces
The interactive browser SHALL show Chinese labels and descriptions for the Help
page, contextual action bar, command palette, and command list.

#### Scenario: Command words remain executable
- **GIVEN** the command list is rendered in Chinese
- **THEN** executable command literals such as `build`, `problems group file`,
  and `copy source` remain unchanged

### Requirement: Source File Page mark-based range selection
The browser SHALL let users select a Source File Page range by marking the
current source target line and selecting to the later current target line.

#### Scenario: Mark current line and select to another current line
- **GIVEN** the browser is on Source File Page at line 5
- **WHEN** the user runs `source mark`
- **AND** the current source target line later becomes 9
- **AND** the user runs `source select to`
- **THEN** the Source File Page selection SHALL be lines 5 through 9
- **AND** `copy source` SHALL keep using the selected range behavior

#### Scenario: Selection works regardless of direction
- **GIVEN** the browser is on Source File Page at line 9 with an active mark
  from line 5
- **WHEN** the current source target line later becomes 3
- **AND** the user runs `source select to`
- **THEN** the Source File Page selection SHALL be lines 3 through 5

#### Scenario: Mark is page-local
- **GIVEN** the browser has a source mark in Source File Page
- **WHEN** the user navigates away and returns through page history
- **THEN** the source mark SHALL be restored
- **WHEN** the user opens a different source file
- **THEN** the source mark SHALL be cleared

### Requirement: Copy visible same-file task problems
The browser SHALL let users copy all currently visible Task Problems that share
the selected problem's file path.

#### Scenario: Copy problems for the selected file
- **GIVEN** Task Problems contains visible problems for `src/A.ets` and
  `src/B.ets`
- **AND** the selected problem is in `src/A.ets`
- **WHEN** the user runs `copy file problems`
- **THEN** the copied Markdown SHALL include only visible problems from
  `src/A.ets`
- **AND** the browser SHALL preserve page, selection, filters, sort, grouping,
  Review Scope, and task state

#### Scenario: Respect current visible filters
- **GIVEN** Task Problems has severity or text filters active
- **WHEN** the user runs `copy file problems`
- **THEN** the copied Markdown SHALL use only the currently visible filtered
  problems for the selected file

#### Scenario: Empty Problems list
- **GIVEN** no Task Problems are currently visible
- **WHEN** the user runs `copy file problems`
- **THEN** the browser SHALL report that there are no task problems to copy

### Requirement: Jump between visible Task Problems files

The browser SHALL let users move the Task Problems selection between file groups in the current visible Problems list.

#### Scenario: Jump to next file
- **GIVEN** Task Problems contains visible problems for `src/A.ets`, `src/B.ets`, and `src/C.ets`
- **AND** the selected problem is in `src/A.ets`
- **WHEN** the user runs `next problem file`
- **THEN** the selected problem SHALL move to the first visible problem in `src/B.ets`
- **AND** the browser SHALL preserve page, filters, sort, grouping, Review Scope, and task state

#### Scenario: Jump to previous file
- **GIVEN** Task Problems contains visible problems for `src/A.ets`, `src/B.ets`, and `src/C.ets`
- **AND** the selected problem is in `src/C.ets`
- **WHEN** the user runs `prev problem file`
- **THEN** the selected problem SHALL move to the first visible problem in `src/B.ets`

#### Scenario: Respect current visible filters
- **GIVEN** Task Problems has severity or text filters active
- **WHEN** the user runs `next problem file` or `prev problem file`
- **THEN** file jumps SHALL consider only the currently visible filtered problems

#### Scenario: Edge file keeps selection
- **GIVEN** the selected problem is already in the first or last visible file group
- **WHEN** the user runs the corresponding previous or next file jump command
- **THEN** the selected problem SHALL stay unchanged
- **AND** the browser SHALL show an explanatory status message

### Requirement: Show changed-file queue inside File Detail

The browser SHALL show a compact changed-file queue dock at the bottom of File Detail when enough vertical space is available.

#### Scenario: Show current file and nearby files
- **GIVEN** File Detail is rendering a selected file from a visible changed-file list
- **WHEN** the page has enough vertical space for the dock
- **THEN** the dock SHALL show the current file position and total visible files
- **AND** it SHALL show nearby changed files
- **AND** it SHALL mark the selected file

#### Scenario: Reuse existing review state
- **GIVEN** changed files have seen state, notes, source labels, and added/deleted counts
- **WHEN** File Detail renders the dock
- **THEN** the dock SHALL show seen/todo state, note marker, source label, and change summary from existing state
- **AND** it SHALL NOT introduce independent dock selection or persistence state

#### Scenario: Preserve small-height rendering
- **GIVEN** File Detail has too little vertical space
- **WHEN** the page renders
- **THEN** the browser SHALL prefer file detail content and omit the dock instead of replacing the diff with queue rows

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

### Requirement: Keep task tail handoff lightweight

Task output tail handoff MUST NOT change task lifecycle, task history, Problems parsing, task output capture capacity, or workspace persistence.

#### Scenario: Tail handoff is a snapshot
- **GIVEN** a task is still running
- **WHEN** the user copies or saves task output tail
- **THEN** the handoff SHALL use the currently captured output snapshot
- **AND** the task SHALL continue running normally

### Requirement: Show current source symbol in Source File Page

The browser SHALL show a best-effort current symbol label in Source File Page when the target line belongs to a parsed source symbol.

#### Scenario: Show enclosing method label
- **GIVEN** Source File Page is showing a repo-local source file
- **AND** the target line is inside a parsed class method
- **WHEN** the page renders
- **THEN** the header SHALL include a readable symbol label for the enclosing method and container

#### Scenario: Omit missing symbol label
- **GIVEN** Source File Page is showing a source line outside parsed symbols
- **WHEN** the page renders
- **THEN** the header SHALL omit the symbol label rather than showing an unknown placeholder

### Requirement: Include current source symbol in source handoff

The browser SHALL include the current symbol label in copied source Markdown when a label is available.

#### Scenario: Copy source context with symbol
- **GIVEN** Source File Page target line belongs to a parsed symbol
- **WHEN** the user runs `copy source` without a selected range
- **THEN** the copied Markdown SHALL include the current symbol label
- **AND** it SHALL keep the existing source context line window unchanged

#### Scenario: Copy selected source range with symbol
- **GIVEN** Source File Page has an active source selection
- **AND** the target line belongs to a parsed symbol
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL include the current symbol label
- **AND** it SHALL keep the selected line range unchanged

### Requirement: Keep source symbol hints lightweight

Current source symbol hints MUST NOT introduce language-server dependencies, syntax-aware range expansion, source editing, workspace persistence, or Source File Page state fields.

#### Scenario: Symbol lookup is informational
- **GIVEN** source symbol parsing fails to identify an enclosing symbol
- **WHEN** Source File Page renders or copies source
- **THEN** source preview and copy behavior SHALL continue without a symbol label

### Requirement: Source File can select the current symbol

The Source File page SHALL provide a command that selects the innermost
best-effort outline symbol containing the current source line.

#### Scenario: Select current method symbol

- **GIVEN** the browser is on Source File for a repo-local ArkTS/ETS/TS file
- **AND** the current line is inside a method parsed by the existing outline module
- **WHEN** the user runs `source select symbol`
- **THEN** the source selection SHALL become that method's start and end line
- **AND** the page SHALL redraw with the selected range visible
- **AND** the status SHALL include the selected symbol label and range

#### Scenario: No source page is open

- **GIVEN** the browser is not on Source File
- **WHEN** the user runs `source select symbol`
- **THEN** no source selection SHALL be changed
- **AND** the status SHALL tell the user to open a source file first

#### Scenario: No symbol contains the current line

- **GIVEN** the browser is on Source File
- **AND** no outline symbol contains the current source line
- **WHEN** the user runs `source select symbol`
- **THEN** no source selection SHALL be changed
- **AND** the status SHALL say no source symbol exists at the current line

### Requirement: Selected symbol range composes with copy source

The command SHALL reuse the existing Source File selection behavior so that a
subsequent `copy source` copies the selected symbol range with symbol metadata.

#### Scenario: Copy selected symbol

- **GIVEN** `source select symbol` selected the current method range
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL contain the selected range header
- **AND** it SHALL include the existing `Symbol: ...` metadata
- **AND** it SHALL not include lines outside the selected symbol range

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

### Requirement: Task Output can hand off first parsed problem context

The Task Output page SHALL allow `copy problem context` and
`save problem context [PATH]` to use the first visible parsed task problem.

#### Scenario: Copy first problem context from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains a repo-local parseable problem
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL contain the selected problem facts
- **AND** it SHALL include source context for that problem line

#### Scenario: Save first problem context from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains a repo-local parseable problem
- **WHEN** the user runs `save problem context PATH`
- **THEN** the same first-problem context SHALL be written to PATH

### Requirement: File Detail can open Source File at current new line

The File Detail page SHALL provide a command that opens the Source File page at
the current rendered new-file line.

#### Scenario: View source from current diff row

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL open Source File for the current changed file
- **AND** the Source File target line SHALL be the mapped new-file line
- **AND** Back SHALL return to the same File Detail scroll

#### Scenario: Current row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row is a deleted-only row or another row without a new-file line
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL remain on File Detail
- **AND** the status SHALL say there is no current new-file line

#### Scenario: Not on File Detail

- **GIVEN** the browser is not on File Detail
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL stay on the current page
- **AND** the status SHALL tell the user to open a file detail first

### Requirement: File Detail can copy source context

The File Detail page SHALL allow `copy source` to copy Source File-style
Markdown for the current rendered new-file line.

#### Scenario: Copy source from current diff row

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line
- **WHEN** the user runs `copy source`
- **THEN** copied Markdown SHALL be anchored to the current changed file and mapped line
- **AND** it SHALL include source context around that line
- **AND** it SHALL include best-effort symbol metadata when available
- **AND** the browser SHALL remain on File Detail

#### Scenario: Current diff row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row has no new-file line
- **WHEN** the user runs `copy source`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say there is no current new-file line

### Requirement: Source File copy source remains unchanged

The existing Source File `copy source` behavior SHALL continue to copy selected
ranges or target-line context as before.

#### Scenario: Copy source from Source File

- **GIVEN** the browser is on Source File
- **WHEN** the user runs `copy source`
- **THEN** the existing Source File copy behavior SHALL be preserved

### Requirement: Source File can copy current symbol

Source File SHALL provide `copy source symbol` to copy the innermost best-effort
symbol range containing the current source line.

#### Scenario: Copy current Source File method

- **GIVEN** the browser is on Source File
- **AND** the current line is inside a parsed method
- **WHEN** the user runs `copy source symbol`
- **THEN** copied Markdown SHALL contain that method's source range
- **AND** it SHALL include `Symbol: ...` metadata
- **AND** it SHALL not change the current source selection

### Requirement: File Detail can copy current row symbol

File Detail SHALL provide `copy source symbol` to copy the innermost best-effort
symbol range containing the current rendered new-file line.

#### Scenario: Copy current File Detail method

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line inside a parsed method
- **WHEN** the user runs `copy source symbol`
- **THEN** copied Markdown SHALL contain that method's source range
- **AND** the browser SHALL remain on File Detail

#### Scenario: Current row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row has no new-file line
- **WHEN** the user runs `copy source symbol`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say there is no current new-file line

### Requirement: Missing symbol is reported

When no best-effort source symbol contains the target line, the command SHALL
not copy text and SHALL tell the user no source symbol exists at the current line.

#### Scenario: Copy symbol outside any parsed symbol

- **GIVEN** the browser is on Source File
- **AND** the current line is not inside any parsed symbol
- **WHEN** the user runs `copy source symbol`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say no source symbol exists at the current line

### Requirement: Problem context includes task output excerpt for task problems

The browser SHALL include a compact Task Output excerpt centered on the
problem's original output line when focused Problem Context Markdown is
generated from a parsed task problem.

#### Scenario: Copy selected task problem context with output excerpt

- **GIVEN** Task Problems has a selected problem parsed from captured task output
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the selected problem, nearby source,
  same-file diff context when available, and a Task Output excerpt containing the
  selected problem output line.

#### Scenario: Save first task-output problem context with output excerpt

- **GIVEN** Task Output has at least one visible parsed problem
- **WHEN** the user runs `save problem context`
- **THEN** the saved Markdown SHALL include a Task Output excerpt centered on the
  first visible parsed problem's output line.

### Requirement: Source page context remains source focused

The browser SHALL NOT add a Task Output excerpt to Problem Context Markdown
generated directly from Source File Page unless an active task problem target is
used.

#### Scenario: Copy source page problem context

- **GIVEN** Source File Page is open for a source file and line
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include source and diff context
- **AND** it SHALL NOT include a Task Output section.

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

### Requirement: Task Output shows selected problem status

Task Output SHALL show a compact selected-problem label when visible parsed
problems exist.

#### Scenario: Render selected problem label

- **GIVEN** Task Output has two visible parsed problems and the second problem is
  selected
- **WHEN** Task Output is rendered
- **THEN** the page SHALL show `Problem: 2/2` and the selected problem location.

### Requirement: Source outline recognizes field arrow-function symbols

The source outline SHALL recognize class, struct, and interface field
arrow-function declarations as method-like symbols when they appear inside a
container.

#### Scenario: Label line inside a field arrow function

- **GIVEN** an ArkTS source file with `private onTap = () => { ... }` inside a
  struct
- **WHEN** the current line is inside the arrow-function body
- **THEN** the symbol label SHALL include `struct ... > method onTap`.

#### Scenario: Copy field arrow function source symbol

- **GIVEN** Source File Page is open on a line inside a field arrow function
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied Markdown SHALL include the full field arrow-function range
- **AND** the symbol metadata SHALL name the field arrow function.

### Requirement: Top-level arrow functions remain function symbols

The source outline SHALL continue to recognize top-level `const name = () =>`
declarations as function symbols.

#### Scenario: Label line inside a top-level arrow function

- **GIVEN** a top-level `const load = () => { ... }` declaration
- **WHEN** the current line is inside the arrow-function body
- **THEN** the symbol label SHALL include `function load`.

### Requirement: Source File supports adjacent symbol navigation

The browser SHALL support jumping to adjacent recognized source symbols from
Source File Page.

#### Scenario: Jump to next symbol

- **GIVEN** Source File Page is open on a line before another recognized symbol
- **WHEN** the user runs `next symbol`
- **THEN** the current source line SHALL move to the next symbol start line
- **AND** the page SHALL remain Source File Page.

#### Scenario: Jump to previous symbol

- **GIVEN** Source File Page is open on a line after a recognized symbol
- **WHEN** the user runs `prev symbol`
- **THEN** the current source line SHALL move to the previous symbol start line
- **AND** the page SHALL remain Source File Page.

### Requirement: Source symbol navigation handles empty and boundary states

The browser SHALL report clear status messages without changing the current
source line when adjacent source-symbol navigation cannot move.

#### Scenario: No next symbol

- **GIVEN** Source File Page is open at or after the final recognized symbol
- **WHEN** the user runs `next symbol`
- **THEN** the browser SHALL report that it is already at the last symbol
- **AND** preserve the current source line.

#### Scenario: No source symbols

- **GIVEN** Source File Page is open for a readable file with no recognized
  symbols
- **WHEN** the user runs `next symbol`
- **THEN** the browser SHALL report that no source symbols were found
- **AND** preserve the current source line.

### Requirement: Source File problem context uses selected source ranges

The browser SHALL use the active Source File selected range when generating
Problem Context Markdown directly from Source File Page.

#### Scenario: Copy selected Source File problem context

- **GIVEN** Source File Page is open with an active selected source range
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the selected source range
- **AND** it SHALL NOT include source lines outside that selected range.

#### Scenario: Save selected Source File problem context

- **GIVEN** Source File Page is open with an active selected source range
- **WHEN** the user runs `save problem context`
- **THEN** the saved Markdown SHALL include the selected source range.

### Requirement: Source File problem context preserves line context fallback

The browser SHALL keep the existing Source File line-context behavior when no
source range is selected.

#### Scenario: Copy unselected Source File problem context

- **GIVEN** Source File Page is open without a selected source range
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the configured source context radius
  around the current source line.

### Requirement: File Detail Handoff Context

The browser SHALL allow users to copy or save an AI handoff context from File Detail using the currently rendered new-file line.

#### Scenario: Copy current File Detail line context

- **GIVEN** the browser is on File Detail for a changed file
- **AND** the current rendered row maps to a new-file source line
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text includes source context for that file and line
- **AND** the copied text includes the same-file diff context
- **AND** the browser remains on File Detail without changing scroll position

#### Scenario: Save current File Detail line context

- **GIVEN** the browser is on File Detail for a changed file
- **AND** the current rendered row maps to a new-file source line
- **WHEN** the user runs `save problem context PATH`
- **THEN** the saved text includes source context for that file and line
- **AND** the saved text includes the same-file diff context

#### Scenario: Deleted-only rows cannot produce source context

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row has no new-file source line
- **WHEN** the user runs `copy problem context` or `save problem context`
- **THEN** no handoff text is copied or saved
- **AND** the browser reports that there is no current new-file line in File Detail

### Requirement: Problem Diff Navigation

The browser SHALL allow users to jump from the selected task problem to that file's diff when the file exists in the current review scope.

#### Scenario: Task Problems opens problem diff

- **GIVEN** the browser is on Task Problems
- **AND** the selected problem path exists in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser opens File Detail for that path
- **AND** File Detail scrolls to the rendered row matching the problem line when available

#### Scenario: Task Output opens selected problem diff

- **GIVEN** the browser is on Task Output
- **AND** a task problem is selected
- **AND** the selected problem path exists in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser opens File Detail for the selected problem path

#### Scenario: Problem file has no current diff

- **GIVEN** the selected task problem path is not in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser does not navigate
- **AND** it reports that no diff is available for the problem location

### Requirement: Accessor and Override Symbol Recognition

The lightweight source outline SHALL recognize common ArkTS/TS override and accessor member declarations as method-like symbols.

#### Scenario: Override method label

- **GIVEN** a class or struct contains `override name(...) { ... }`
- **WHEN** cr asks for the symbol label at a line inside that method
- **THEN** the label includes the containing class/struct and `method name`

#### Scenario: Getter and setter labels

- **GIVEN** a class or struct contains `get name() { ... }` or `set name(value) { ... }`
- **WHEN** cr asks for the symbol label at a line inside the accessor
- **THEN** the label includes the containing class/struct and `method name`

#### Scenario: Copy source symbol uses accessor range

- **GIVEN** Source File is focused on a line inside an accessor
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied source range contains that accessor block
- **AND** it does not include adjacent methods outside the accessor

### Requirement: Generic Symbol Recognition

The lightweight source outline SHALL recognize common ArkTS/TS generic function-like declarations as symbols.

#### Scenario: Generic method label

- **GIVEN** a class or struct contains `name<T>(...) { ... }`
- **WHEN** cr asks for the symbol label at a line inside that method
- **THEN** the label includes the containing class/struct and `method name`

#### Scenario: Generic function label

- **GIVEN** a source file contains `function name<T>(...) { ... }`
- **WHEN** cr asks for the symbol label at a line inside that function
- **THEN** the label is `function name`

#### Scenario: Generic arrow function label

- **GIVEN** a source file contains `const name = <T>(...) => { ... }`
- **WHEN** cr asks for the symbol label at a line inside that arrow function
- **THEN** the label is `function name`

#### Scenario: Copy source symbol uses generic method range

- **GIVEN** Source File is focused on a line inside a generic method
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied source range contains that generic method block
- **AND** it does not include adjacent methods outside the generic method

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

### Requirement: Recognize exported arrow function declarations

The lightweight source outline SHALL recognize top-level exported `const`, `let`, and `var` arrow declarations as function symbols.

#### Scenario: Exported const arrow

- **GIVEN** a source file contains `export const loadModel = async <T>(value: T) => { ... }`
- **WHEN** the outline is queried for a line inside that function body
- **THEN** the symbol label is `function loadModel`.

#### Scenario: Exported let arrow

- **GIVEN** a source file contains `export let normalize = (value: string) => { ... }`
- **WHEN** the outline is queried for a line inside that function body
- **THEN** the symbol label is `function normalize`.

### Requirement: Recognize named default-exported containers

The lightweight source outline SHALL recognize named `export default class`, `export default struct`, and `export default interface` declarations as container symbols.

#### Scenario: Default-exported class

- **GIVEN** a source file contains `export default class FeedStore { hydrate() { ... } }`
- **WHEN** the outline is queried for a line inside `hydrate`
- **THEN** the symbol label is `class FeedStore > method hydrate`.

### Requirement: Recognize named default-exported functions

The lightweight source outline SHALL recognize named `export default function` declarations as function symbols.

#### Scenario: Default-exported function

- **GIVEN** a source file contains `export default function createStore() { ... }`
- **WHEN** the outline is queried for a line inside that function body
- **THEN** the symbol label is `function createStore`.

### Requirement: Save current Task Problems list

The browser SHALL support saving the current visible Task Problems list as Markdown.

#### Scenario: Save default problems list

- **GIVEN** the current task output contains visible problems
- **WHEN** the user runs `save problems`
- **THEN** the current visible problem list is saved to `.cr/handoff/task-problems.md`
- **AND** the browser reports the number of saved problems.

### Requirement: Save selected-file Task Problems list

The browser SHALL support saving visible Task Problems for the selected problem's file.

#### Scenario: Save file-specific problems list

- **GIVEN** the current visible problem list contains multiple files
- **AND** the selected problem belongs to `src/Two.ets`
- **WHEN** the user runs `save file problems tmp/two-problems.md`
- **THEN** only visible problems from `src/Two.ets` are saved to `tmp/two-problems.md`
- **AND** the browser reports the number of saved problems and selected path.

### Requirement: Save current source context

The browser SHALL support saving the same Markdown handoff produced by `copy source`.

#### Scenario: Save selected Source File range

- **GIVEN** Source File has an active selected range
- **WHEN** the user runs `save source`
- **THEN** the selected source range is saved to `.cr/handoff/source.md`
- **AND** the current target line remains marked in the saved Markdown.

### Requirement: Save current source symbol

The browser SHALL support saving the same Markdown handoff produced by `copy source symbol`.

#### Scenario: Save File Detail source symbol

- **GIVEN** File Detail is focused on a changed source line inside a recognized symbol
- **WHEN** the user runs `save source symbol tmp/render.md`
- **THEN** the current symbol range is saved to `tmp/render.md`
- **AND** the browser remains on File Detail without mutating Source File selection.

### Requirement: Open current Source File diff

The browser SHALL let Source File users open the current source path in File Detail for the active review scope.

#### Scenario: Source File current line exists in diff

- **GIVEN** Source File is open for `src/Foo.ets` at line 12
- **AND** `src/Foo.ets` is present in the current changed-file list
- **WHEN** the user runs `view diff`
- **THEN** the browser opens File Detail for `src/Foo.ets`
- **AND** scrolls to the rendered diff row for line 12 when visible.

#### Scenario: Source File path is not changed

- **GIVEN** Source File is open for `src/Unchanged.ets`
- **AND** `src/Unchanged.ets` is not present in the current changed-file list
- **WHEN** the user runs `view diff`
- **THEN** the browser stays on Source File
- **AND** reports that no diff is available in the current review scope.

### Requirement: Step between task problems from Source File

The browser SHALL let Source File users step to adjacent parsed task problems without returning to Task Output or Task Problems.

#### Scenario: Move to next problem source

- **GIVEN** Source File is showing the selected task problem source
- **WHEN** the user runs `next problem`
- **THEN** Source File updates to the next task problem path and line
- **AND** the page remains Source File.

#### Scenario: Move to previous problem source

- **GIVEN** Source File is showing a later task problem source
- **WHEN** the user runs `prev problem`
- **THEN** Source File updates to the previous task problem path and line
- **AND** the page remains Source File.

#### Scenario: Preserve page history

- **GIVEN** Source File was opened from Task Problems
- **WHEN** the user runs `next problem`
- **AND** then returns with `b`
- **THEN** the browser returns to Task Problems, not to the previous Source File problem.

### Requirement: Show current task problem on Source File

The browser SHALL show a compact current task problem label on Source File when the current source target corresponds to the selected parsed task problem.

#### Scenario: Matching task problem

- **GIVEN** Source File is open at `src/Foo.ets:12`
- **AND** the selected parsed task problem is also `src/Foo.ets:12`
- **WHEN** the Source File page renders
- **THEN** the header includes a compact task problem label.

#### Scenario: Stale selected problem

- **GIVEN** Source File is open at `src/Foo.ets:20`
- **AND** the selected parsed task problem is `src/Foo.ets:12`
- **WHEN** the Source File page renders
- **THEN** the header does not show that stale task problem label.

### Requirement: Copy current Source File task problem

The browser SHALL let Source File users copy the task problem represented by the current source target.

#### Scenario: Matching current problem

- **GIVEN** Source File is open at `src/Foo.ets:12`
- **AND** the selected parsed task problem is also `src/Foo.ets:12`
- **WHEN** the user runs `copy problem`
- **THEN** the browser copies that task problem handoff text.

#### Scenario: Stale selected problem

- **GIVEN** Source File is open at `src/Foo.ets:20`
- **AND** the selected parsed task problem is `src/Foo.ets:12`
- **WHEN** the user runs `copy problem`
- **THEN** the browser does not copy the stale selected problem
- **AND** reports that no current source problem is available.

### Requirement: Save Current Task Problem

The browser SHALL support saving the current single task problem as Markdown.

#### Scenario: Save selected problem from Task Problems

- **GIVEN** Task Problems has visible parsed problems
- **AND** one problem is selected
- **WHEN** the user runs `save problem`
- **THEN** cr writes that problem to `.cr/handoff/task-problem.md`
- **AND** the browser stays on Task Problems with selection preserved

#### Scenario: Save selected problem to requested path

- **GIVEN** a current task problem exists
- **WHEN** the user runs `save problem tmp/problem.md`
- **THEN** cr writes that problem to `tmp/problem.md`

#### Scenario: Refuse stale Source File problem

- **GIVEN** Source File is open
- **AND** the selected parsed problem no longer exactly matches the current source path and line
- **WHEN** the user runs `save problem`
- **THEN** cr does not write a file
- **AND** reports that there is no current source problem to save

### Requirement: Copy Current Problem Diff

The browser SHALL copy a lightweight file diff snippet for the current task problem when that problem belongs to a file in the current review scope.

#### Scenario: Copy selected problem diff from Task Problems

- **GIVEN** Task Problems has a selected parsed problem
- **AND** the problem path exists in the current review scope
- **WHEN** the user runs `copy problem diff`
- **THEN** cr copies a file diff snippet for that path
- **AND** the browser stays on the current page with selection preserved

#### Scenario: Refuse problem diff outside review scope

- **GIVEN** the current task problem path is not in the current review scope
- **WHEN** the user runs `copy problem diff`
- **THEN** cr does not copy text
- **AND** reports that no diff exists for that problem in the current review scope

### Requirement: Save Current Problem Diff

The browser SHALL save the current problem's lightweight file diff snippet as Markdown.

#### Scenario: Save current problem diff to default path

- **GIVEN** a current task problem has a changed file in the current review scope
- **WHEN** the user runs `save problem diff`
- **THEN** cr writes `.cr/handoff/problem-diff.md`

#### Scenario: Refuse stale Source File problem diff

- **GIVEN** Source File is open
- **AND** the selected parsed problem no longer exactly matches the current source path and line
- **WHEN** the user runs `save problem diff`
- **THEN** cr does not write a file
- **AND** reports that there is no current source problem diff to save

### Requirement: Save Review Notes Summary

The browser SHALL save the current Review Notes summary as Markdown-like plain text.

#### Scenario: Save notes to default path

- **GIVEN** the workspace has review notes
- **WHEN** the user runs `save notes`
- **THEN** cr writes `.cr/handoff/review-notes.md`
- **AND** the file uses the same ordered summary as `notes` and `copy notes`
- **AND** the browser keeps the current page, selection, task state, filters, and review progress

#### Scenario: Save notes to requested path

- **GIVEN** the workspace has review notes
- **WHEN** the user runs `save notes tmp/notes.md`
- **THEN** cr writes `tmp/notes.md`

#### Scenario: No notes to save

- **GIVEN** the workspace has no review notes
- **WHEN** the user runs `save notes`
- **THEN** cr does not write a file
- **AND** reports `No review notes to save.`

### Requirement: Open current File Detail source symbol

The browser SHALL let File Detail users open the current new-file source line in Source File and select the enclosing lightweight source symbol.

#### Scenario: Current diff row is inside a source symbol

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** the current rendered row maps to new-file line 12
- **AND** line 12 is inside a recognized function or method
- **WHEN** the user runs `view source symbol`
- **THEN** the browser opens Source File for `src/Foo.ets` at line 12
- **AND** selects the recognized enclosing symbol range.

#### Scenario: Current diff row has no new-file line

- **GIVEN** File Detail is open for a deleted-only or metadata row
- **WHEN** the user runs `view source symbol`
- **THEN** the browser stays on File Detail
- **AND** reports that there is no current new-file line.

#### Scenario: Current source line has no recognized symbol

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** the current rendered row maps to a new-file line
- **AND** that source line is not inside a recognized lightweight source symbol
- **WHEN** the user runs `view source symbol`
- **THEN** the browser opens Source File at that line
- **AND** reports that no source symbol is available without creating a fake selection.

### Requirement: Declaration Source Symbol Recognition

The lightweight source outline SHALL recognize common ArkTS/TS declaration-only function-like members without letting them capture unrelated following code.

#### Scenario: Abstract method label

- **GIVEN** a class contains `abstract load(): Promise<void>;`
- **WHEN** cr asks for the symbol label at that declaration line
- **THEN** the label includes the containing class and `method load`.

#### Scenario: Abstract accessor label

- **GIVEN** a class contains `abstract get title(): string;`
- **WHEN** cr asks for the symbol label at that declaration line
- **THEN** the label includes the containing class and `method title`.

#### Scenario: Declaration-only member does not capture following method

- **GIVEN** a class contains a declaration-only member followed by a concrete method
- **WHEN** cr asks for the symbol label inside the concrete method
- **THEN** the label resolves to the concrete method, not the earlier declaration-only member.

#### Scenario: Interface method declarations remain one-line symbols

- **GIVEN** an interface contains multiple method declarations
- **WHEN** cr asks for the symbol label at the second declaration
- **THEN** the label resolves to the second declaration, not the first one.

### Requirement: Step Current File Problems In File Detail

The browser SHALL let File Detail users step through parsed task problems for the current changed file without leaving File Detail.

#### Scenario: Next problem line is visible in current diff

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include multiple entries for `src/Foo.ets`
- **AND** the next selected problem line is visible in the rendered File Detail diff
- **WHEN** the user runs `next problem`
- **THEN** the browser keeps File Detail open
- **AND** updates the selected task problem
- **AND** scrolls to the rendered diff row for that problem line.

#### Scenario: Problem line is not visible in current diff

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include an entry for `src/Foo.ets`
- **AND** that problem line is not visible in the rendered File Detail diff
- **WHEN** the user runs `next problem`
- **THEN** the browser keeps File Detail open
- **AND** updates the selected task problem
- **AND** reports that the problem line is not visible in the current diff.

#### Scenario: Current file has no task problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** no parsed task problem belongs to `src/Foo.ets`
- **WHEN** the user runs `next problem`
- **THEN** the browser keeps File Detail open
- **AND** reports that the current file has no task problems.

### Requirement: File Detail Current File Problems Handoff

The browser SHALL scope file-problem handoff commands to the current changed file when the user is in File Detail.

#### Scenario: Copy current File Detail file problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include entries for `src/Foo.ets` and `src/Bar.ets`
- **AND** the globally selected task problem belongs to `src/Bar.ets`
- **WHEN** the user runs `copy file problems`
- **THEN** the copied handoff includes only problems for `src/Foo.ets`.

#### Scenario: Save current File Detail file problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include entries for `src/Foo.ets`
- **WHEN** the user runs `save file problems tmp/foo.md`
- **THEN** the saved handoff contains problems for `src/Foo.ets`.

#### Scenario: Current File Detail file has no problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems contain no entries for `src/Foo.ets`
- **WHEN** the user runs `copy file problems`
- **THEN** the browser reports that the current file has no task problems.

### Requirement: Copy or save current File Detail row problem

The browser SHALL let File Detail users copy or save the single task problem that exactly matches the current changed file and rendered new-file line.

#### Scenario: Current diff row matches a task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **AND** the globally selected task problem points at another file
- **WHEN** the user runs `copy problem`
- **THEN** the browser copies the `src/One.ets:4` problem
- **AND** it does not copy the globally selected problem.

#### Scenario: Save current diff row problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem tmp/problem.md`
- **THEN** the browser writes a single-problem handoff file for `src/One.ets:4`.

#### Scenario: Current diff row has no matching problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem`
- **THEN** the browser refuses the command
- **AND** it does not fall back to any globally selected task problem.

### Requirement: Copy or save current File Detail row problem diff

The browser SHALL let File Detail users copy or save the changed-file diff for the task problem that exactly matches the current changed file and rendered new-file line.

#### Scenario: Current diff row problem diff is copied

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **AND** the globally selected task problem points at another file
- **WHEN** the user runs `copy problem diff`
- **THEN** the browser copies the diff for `src/One.ets`
- **AND** it does not copy the globally selected problem's file diff.

#### Scenario: Current diff row problem diff is saved

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem diff tmp/problem-diff.md`
- **THEN** the browser writes the changed-file diff for `src/One.ets`.

#### Scenario: Current diff row has no matching problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem diff`
- **THEN** the browser refuses the command
- **AND** it does not fall back to any globally selected task problem.

### Requirement: Enrich File Detail problem context with current-row task problem

The browser SHALL include problem text and nearby task output in File Detail problem context handoff when the current rendered new-file line exactly matches a parsed task problem.

#### Scenario: Current File Detail row matches a task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes a `Problem` section for `src/One.ets:4`
- **AND** includes a nearby `Task Output` excerpt
- **AND** includes the current source context and changed-file diff.

#### Scenario: Current File Detail row has no matching task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context still includes source and diff
- **AND** it does not include any globally selected task problem.

#### Scenario: Save enriched File Detail problem context

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem context tmp/context.md`
- **THEN** the saved context includes the current problem, task output excerpt, source, and diff.

### Requirement: Enrich Source File problem context with current task problem

The browser SHALL include problem text and nearby task output in Source File problem context handoff when the current source line exactly matches the selected parsed task problem.

#### Scenario: Current Source File line matches a task problem

- **GIVEN** Source File is open for `src/Foo.ets` at line 5
- **AND** the selected task problem is exactly `src/Foo.ets:5`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes a `Problem` section
- **AND** includes a nearby `Task Output` excerpt
- **AND** includes the current source context and changed-file diff.

#### Scenario: Source selection is active

- **GIVEN** Source File is open for `src/Foo.ets` at line 5
- **AND** the selected task problem is exactly `src/Foo.ets:5`
- **AND** a source range is selected
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes the selected source range
- **AND** still includes the current problem and task output excerpt.

#### Scenario: Current Source File line has no matching problem

- **GIVEN** Source File is open for `src/Foo.ets` at line 8
- **AND** the selected task problem points at another line or file
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context still includes source and diff
- **AND** it does not include the stale selected task problem.

### Requirement: Enum Symbol Recognition

The lightweight source outline SHALL recognize common TS/ArkTS enum declarations as block-level source symbols.

#### Scenario: Exported const enum label

- **GIVEN** a source file contains `export const enum FeedStatus { ... }`
- **WHEN** cr asks for the symbol label at a line inside that enum body
- **THEN** the label is `enum FeedStatus`

#### Scenario: Exported enum label

- **GIVEN** a source file contains `export enum LoadState { ... }`
- **WHEN** cr asks for the symbol label at a line inside that enum body
- **THEN** the label is `enum LoadState`

#### Scenario: Plain enum label

- **GIVEN** a source file contains `enum CardKind { ... }`
- **WHEN** cr asks for the symbol label at a line inside that enum body
- **THEN** the label is `enum CardKind`

#### Scenario: Modified enum name

- **GIVEN** a changed line belongs to an enum body
- **WHEN** cr maps changed lines to modified source symbols
- **THEN** the enum name is returned instead of `unknown`

#### Scenario: Copy source symbol uses enum range

- **GIVEN** Source File is focused on a line inside an enum body
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied source range contains that enum block
- **AND** it does not include the following top-level symbol

### Requirement: Prompt renderer includes supplied review notes
The prompt renderer SHALL render supplied per-file review notes as part of the canonical Markdown handoff.

#### Scenario: Render file review note in summary and detail
- **WHEN** review data for a file contains `review_note`
- **THEN** `render_prompt_handoff` SHALL render `review note: ...` for that file under `## Files`
- **AND** SHALL render `review note: ...` for that file under `## Details`

#### Scenario: Preserve prompt format without notes
- **WHEN** review data contains no `review_note`
- **THEN** `render_prompt_handoff` SHALL preserve the existing no-note prompt structure

### Requirement: Browser opens selected files in an editor
The browser SHALL provide an `open` command that opens the selected changed file through the configured or platform editor command.

#### Scenario: Open selected file
- **WHEN** the user runs `open` with a changed file selected
- **THEN** the browser SHALL resolve the repository file path
- **AND** SHALL pass the first changed line when available
- **AND** SHALL launch the resolved editor command
- **AND** SHALL show feedback through the existing browser message/status area

#### Scenario: Open selected file with no file
- **WHEN** the user runs `open` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without changing page state

### Requirement: File actions module owns platform action details
The file actions module SHALL own command source resolution, platform fallback, template expansion, subprocess launch, and failure messages for open, copy, and reveal file actions.

#### Scenario: Resolve open source from file actions module
- **WHEN** open command diagnostics or execution need an editor command
- **THEN** the source SHALL be resolved through `cr.ui.file_actions`
- **AND** the source SHALL identify `cli`, `env`, `platform`, or `missing`
- **AND** browser action execution SHALL NOT duplicate editor fallback rules
