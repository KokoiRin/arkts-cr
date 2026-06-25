## ADDED Requirements

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
