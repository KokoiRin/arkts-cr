## ADDED Requirements

### Requirement: Browser summarizes review notes
The browser SHALL provide a command that lists all current review notes without changing the active review layer.

#### Scenario: Show ordered review notes
- **WHEN** the user runs `notes`
- **AND** review notes exist for changed files in the active review scope
- **THEN** the browser SHALL show a `Review notes:` summary
- **AND** notes for current changed files SHALL be ordered by the current review list order
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Show persisted notes outside current changes
- **WHEN** the user runs `notes`
- **AND** `review_notes` contains paths that are not in the active changed files
- **THEN** the browser SHALL include those notes after current changed-file notes
- **AND** those extra notes SHALL be ordered by path

#### Scenario: Show empty review notes state
- **WHEN** the user runs `notes`
- **AND** no review notes exist
- **THEN** the browser SHALL show a clear empty state
