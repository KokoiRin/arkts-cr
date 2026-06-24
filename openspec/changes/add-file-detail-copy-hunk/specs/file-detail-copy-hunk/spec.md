## ADDED Requirements

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
