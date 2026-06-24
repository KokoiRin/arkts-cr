## ADDED Requirements

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
