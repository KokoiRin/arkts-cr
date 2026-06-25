## ADDED Requirements

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
