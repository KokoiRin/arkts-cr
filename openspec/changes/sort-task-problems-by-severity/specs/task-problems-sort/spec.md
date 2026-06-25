## ADDED Requirements

### Requirement: Browser optionally sorts Task Problems by severity

The browser SHALL support an explicit severity sort mode for current Task Problems while keeping output order as the default.

#### Scenario: Sort by severity

- **GIVEN** Task Problems include warnings, errors, notes, and unknown-severity anchors
- **WHEN** the user runs `problems sort severity`
- **THEN** the browser SHALL show errors before warnings, info, notes, and unknown anchors
- **AND** it SHALL preserve task-output order within each severity bucket.

#### Scenario: Restore output order

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the user runs `problems sort output`
- **THEN** the browser SHALL show problems in task-output order.

### Requirement: Browser applies sort mode to visible problem actions

The browser SHALL apply the active sort mode to selection, open, source preview, and copy actions.

#### Scenario: Copy sorted visible problems

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the user runs `copy problems`
- **THEN** the copied handoff SHALL follow the sorted visible order.

#### Scenario: Header shows active sort

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the page renders
- **THEN** the header SHALL show that severity sort is active.
