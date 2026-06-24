## ADDED Requirements

### Requirement: Browser filters review notes by query
The browser SHALL provide a command that filters the review notes summary by path or note text.

#### Scenario: Match note text
- **WHEN** the user runs `notes lifecycle`
- **AND** a review note contains `lifecycle`
- **THEN** the browser SHALL show only matching notes
- **AND** SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Match path text case-insensitively
- **WHEN** the user runs `notes sample`
- **AND** a review note path contains `Sample` with different casing
- **THEN** the browser SHALL include that note

#### Scenario: No filtered matches
- **WHEN** the user runs `notes owner`
- **AND** review notes exist but none match `owner`
- **THEN** the browser SHALL show a clear no-match state

#### Scenario: Empty query keeps existing summary
- **WHEN** the user runs `notes`
- **THEN** the browser SHALL keep showing all review notes
