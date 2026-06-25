## ADDED Requirements

### Requirement: Browser filters Task Problems by severity

The browser SHALL filter current Task Problems by extracted severity without reordering them.

#### Scenario: Show error problems only

- **GIVEN** current task output has error and warning problems
- **WHEN** the user runs `problems errors`
- **THEN** the browser SHALL enter Task Problems page
- **AND** it SHALL show only problems whose severity is `error`
- **AND** it SHALL preserve task-output order among visible error problems.

#### Scenario: Clear severity filter

- **GIVEN** Task Problems page is filtered to warnings
- **WHEN** the user runs `problems all`
- **THEN** the browser SHALL show all current task problems.

### Requirement: Browser applies the visible problem filter to actions

The browser SHALL apply the active severity filter to selection, open, source preview, and copy actions.

#### Scenario: Copy visible filtered problems

- **GIVEN** Task Problems page is filtered to errors
- **WHEN** the user runs `copy problems`
- **THEN** the copied handoff SHALL include only visible error problems.

#### Scenario: Empty filtered state

- **GIVEN** current task output has problems but none match the active severity filter
- **WHEN** Task Problems page renders
- **THEN** it SHALL show a filter-specific empty state.
