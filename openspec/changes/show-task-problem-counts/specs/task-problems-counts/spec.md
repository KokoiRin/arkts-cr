## ADDED Requirements

### Requirement: Browser shows Task Problems severity counts

The browser SHALL show compact severity counts for the currently visible Task Problems list.

#### Scenario: Render mixed severity counts

- **GIVEN** Task Problems page has visible errors, warnings, and unknown-severity problems
- **WHEN** the page renders
- **THEN** the header SHALL include counts for each visible severity bucket
- **AND** unknown-severity problems SHALL be counted as `unknown`.

#### Scenario: Filtered counts are visible counts

- **GIVEN** Task Problems page is filtered to errors
- **WHEN** the page renders
- **THEN** the header SHALL show the visible error count
- **AND** it SHALL not imply hidden warning or info totals.
