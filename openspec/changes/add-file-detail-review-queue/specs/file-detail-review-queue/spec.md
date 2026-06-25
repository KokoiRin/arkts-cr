## ADDED Requirements

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
