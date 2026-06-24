## ADDED Requirements

### Requirement: Browser records per-file review notes
The browser SHALL let users set or replace one note for the currently selected changed file.

#### Scenario: Set selected file note
- **WHEN** the user runs `note check lifecycle edge case`
- **AND** a changed file is selected
- **THEN** the selected file SHALL store the note text `check lifecycle edge case`
- **AND** the browser SHALL remain in the current review context
- **AND** SHALL NOT start or stop any task process

### Requirement: Browser clears selected file notes
The browser SHALL let users clear the currently selected file note without editing persisted JSON by hand.

#### Scenario: Clear selected file note
- **WHEN** the selected file already has a note
- **AND** the user runs `note`
- **THEN** the selected file note SHALL be removed
- **AND** the browser SHALL report that the note was cleared

### Requirement: Browser renders review notes in review layers
The browser SHALL surface review notes where users scan and read changed files.

#### Scenario: Show note in changed files and file detail
- **WHEN** a changed file has a note
- **THEN** the Changed Files row SHALL show a compact note marker
- **AND** the File Detail header area SHALL show the full note text

### Requirement: Browser persists review notes with workspace state
The browser SHALL save and restore per-file review notes in the default workspace state.

#### Scenario: Restore saved note
- **WHEN** `.git/cr/browse-state.json` contains `review_notes` for a changed file
- **AND** the next default browser session restores workspace state
- **THEN** the restored browser state SHALL include that file note
- **AND** task history SHALL remain excluded from workspace persistence
