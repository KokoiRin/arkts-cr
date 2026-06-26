# File Detail Reading Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Per-file diff reading, hunk navigation, line/change actions, and File Detail problem handoff.

## Requirements
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

### Requirement: File Detail find behavior remains stable

Extracting shared rendered-text search SHALL preserve File Detail find behavior.

#### Scenario: File Detail find still searches rendered detail text

- **GIVEN** File Detail is visible
- **WHEN** the user runs `find TEXT`, `next match`, or `prev match`
- **THEN** the browser SHALL keep the same File Detail messages, scroll behavior, and `file_find_text` behavior as before

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
