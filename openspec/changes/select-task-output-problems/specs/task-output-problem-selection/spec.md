## ADDED Requirements

### Requirement: Task Output supports selected problem navigation

The browser SHALL support moving the current parsed task-problem selection from
Task Output without requiring users to open Task Problems.

#### Scenario: Move to next parsed problem from Task Output

- **GIVEN** Task Output has multiple visible parsed problems
- **WHEN** the user runs `next problem`
- **THEN** the browser SHALL select the next visible problem
- **AND** keep the current page on Task Output.

#### Scenario: Move to previous parsed problem from Task Output

- **GIVEN** Task Output has multiple visible parsed problems and the second
  problem is selected
- **WHEN** the user runs `prev problem`
- **THEN** the browser SHALL select the previous visible problem
- **AND** keep the current page on Task Output.

### Requirement: Task Output handoff uses selected problem

Task Output problem actions SHALL target the current visible parsed problem
selection.

#### Scenario: View selected Task Output problem source

- **GIVEN** Task Output has multiple visible parsed problems and the second
  problem is selected
- **WHEN** the user runs `view problem`
- **THEN** Source File Page SHALL open at the second problem's source location.

#### Scenario: Copy selected Task Output problem context

- **GIVEN** Task Output has multiple visible parsed problems and the second
  problem is selected
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL describe the second problem.

### Requirement: Task Output shows selected problem status

Task Output SHALL show a compact selected-problem label when visible parsed
problems exist.

#### Scenario: Render selected problem label

- **GIVEN** Task Output has two visible parsed problems and the second problem is
  selected
- **WHEN** Task Output is rendered
- **THEN** the page SHALL show `Problem: 2/2` and the selected problem location.
