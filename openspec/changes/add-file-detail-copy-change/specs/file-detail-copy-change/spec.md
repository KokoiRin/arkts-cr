## ADDED Requirements

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
