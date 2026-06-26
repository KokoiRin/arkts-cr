# Review Scope and Workspace Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Choosing review scopes, preserving workspace state, progress markers, and commit selection.

## Requirements
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
