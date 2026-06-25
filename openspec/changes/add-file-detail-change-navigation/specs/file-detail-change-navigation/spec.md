## ADDED Requirements

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
