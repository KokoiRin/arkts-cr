## ADDED Requirements

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
