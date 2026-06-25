## ADDED Requirements

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
