## ADDED Requirements

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
