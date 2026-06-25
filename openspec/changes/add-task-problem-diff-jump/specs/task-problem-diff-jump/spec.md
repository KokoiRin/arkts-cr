# task-problem-diff-jump Specification

## ADDED Requirements

### Requirement: Problem Diff Navigation

The browser SHALL allow users to jump from the selected task problem to that file's diff when the file exists in the current review scope.

#### Scenario: Task Problems opens problem diff

- **GIVEN** the browser is on Task Problems
- **AND** the selected problem path exists in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser opens File Detail for that path
- **AND** File Detail scrolls to the rendered row matching the problem line when available

#### Scenario: Task Output opens selected problem diff

- **GIVEN** the browser is on Task Output
- **AND** a task problem is selected
- **AND** the selected problem path exists in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser opens File Detail for the selected problem path

#### Scenario: Problem file has no current diff

- **GIVEN** the selected task problem path is not in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser does not navigate
- **AND** it reports that no diff is available for the problem location
