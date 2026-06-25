## ADDED Requirements

### Requirement: Browser filters Task Problems by text

The browser SHALL support a page-local text filter over current Task Problems.

#### Scenario: Filter by query

- **GIVEN** Task Problems include multiple paths and messages
- **WHEN** the user runs `problems find Foo`
- **THEN** the browser SHALL show only problems whose path, location, summary, severity, code, or message contains `Foo` case-insensitively.

#### Scenario: Clear query

- **GIVEN** Task Problems has an active text query
- **WHEN** the user runs `problems clear find`
- **THEN** the browser SHALL clear the query and show problems using the remaining filters and sort mode.

### Requirement: Text filter composes with existing Task Problems view state

The browser SHALL apply the text query after severity filtering and before sorting.

#### Scenario: Actions use queried visible list

- **GIVEN** Task Problems has an active text query
- **WHEN** the user runs `copy problem`, `copy problems`, `view problem`, or opens a problem
- **THEN** the action SHALL use the queried visible list.

#### Scenario: Header shows query

- **GIVEN** Task Problems has an active text query
- **WHEN** the page renders
- **THEN** the header SHALL show the active query.

#### Scenario: Page history restores query

- **GIVEN** Task Problems has an active text query
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active query SHALL be restored.
