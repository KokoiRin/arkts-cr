# Changed Files and File Actions Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Changed-file list behavior, source filters, selected-file actions, and editor/file handoff.

## Requirements
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

### Requirement: Built-in file action fallbacks remain
The browser SHALL preserve built-in platform copy and reveal fallbacks when no configured command is present.

#### Scenario: No configured file action command
- **WHEN** no CLI argument or environment variable is set for a file action
- **THEN** the existing platform fallback behavior SHALL remain available

### Requirement: Browser shows file action diagnostics
The browser SHALL provide a `file actions` command that explains the resolved source for open, copy, and reveal actions.

#### Scenario: Show unified action sources
- **WHEN** the user runs `file actions`
- **THEN** the browser SHALL show one diagnostic line for `open`
- **AND** SHALL show one diagnostic line for `copy`
- **AND** SHALL show one diagnostic line for `reveal`
- **AND** SHALL NOT execute any file action

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

### Requirement: Editor handoff failures include source context
The browser SHALL include resolved command source context when editor handoff cannot run.

#### Scenario: Open command fails
- **WHEN** `open` resolves to a command
- **AND** the command fails to launch
- **THEN** the user-visible failure message SHALL include the source and command summary

#### Scenario: Open command is missing
- **WHEN** no open command can be resolved
- **THEN** the user-visible failure message SHALL include that the source is `missing`

### Requirement: Save selected file prompt handoff
The browser SHALL support `save prompt file [PATH]` to write prompt-ready Markdown for only the selected visible changed file to a file.

#### Scenario: Save selected file to default path
- **WHEN** the current browser scope has a selected visible changed file and the user runs `save prompt file`
- **THEN** the browser SHALL write the same prompt-ready Markdown used by `copy prompt file` to `.cr/handoff/review-prompt-file.md`
- **AND** the generated handoff SHALL include review notes only for the selected file

#### Scenario: Save selected file to explicit path
- **WHEN** the current browser scope has a selected visible changed file and the user runs `save prompt file tmp/file.md`
- **THEN** the browser SHALL write the selected-file prompt-ready Markdown to `tmp/file.md` relative to the repository root

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

### Requirement: File action failures include source context
The browser SHALL include resolved command source context when a file action cannot run.

#### Scenario: Copy command fails
- **WHEN** `copy path` resolves to a configured command
- **AND** the command fails to launch or returns failure
- **THEN** the user-visible failure message SHALL include the source and command summary

#### Scenario: Reveal command is missing
- **WHEN** `reveal` has no configured command and no platform fallback
- **THEN** the user-visible failure message SHALL include that the source is `missing`

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

### Requirement: Selected File Actions Module Ownership

`cr browse` selected-file action workflow MUST be owned by a dedicated UI module rather than browser command execution.

#### Scenario: Browser executes selected-file workflow through a module

- **GIVEN** a parsed browser action such as open, copy path, copy anchor, reveal, note, copy prompt file, or save prompt file
- **WHEN** the action depends on the current selected changed file or current visible changed-file set
- **THEN** selected-file path/line/note/prompt workflow is performed by the Selected File Actions module
- **AND** BrowserCommandExecutor remains responsible for routing parsed commands and placing returned messages into the browser UI
- **AND** platform subprocess details remain owned by `cr.ui.file_actions`
- **AND** prompt Markdown rendering remains owned by `cr.review.prompt`

### Requirement: File actions module owns platform action details
The file actions module SHALL own command source resolution, platform fallback, template expansion, subprocess launch, and failure messages for open, copy, and reveal file actions.

#### Scenario: Resolve open source from file actions module
- **WHEN** open command diagnostics or execution need an editor command
- **THEN** the source SHALL be resolved through `cr.ui.file_actions`
- **AND** the source SHALL identify `cli`, `env`, `platform`, or `missing`
- **AND** browser action execution SHALL NOT duplicate editor fallback rules
