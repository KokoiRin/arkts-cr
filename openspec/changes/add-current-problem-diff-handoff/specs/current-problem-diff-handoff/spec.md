## ADDED Requirements

### Requirement: Copy Current Problem Diff

The browser SHALL copy a lightweight file diff snippet for the current task problem when that problem belongs to a file in the current review scope.

#### Scenario: Copy selected problem diff from Task Problems

- **GIVEN** Task Problems has a selected parsed problem
- **AND** the problem path exists in the current review scope
- **WHEN** the user runs `copy problem diff`
- **THEN** cr copies a file diff snippet for that path
- **AND** the browser stays on the current page with selection preserved

#### Scenario: Refuse problem diff outside review scope

- **GIVEN** the current task problem path is not in the current review scope
- **WHEN** the user runs `copy problem diff`
- **THEN** cr does not copy text
- **AND** reports that no diff exists for that problem in the current review scope

### Requirement: Save Current Problem Diff

The browser SHALL save the current problem's lightweight file diff snippet as Markdown.

#### Scenario: Save current problem diff to default path

- **GIVEN** a current task problem has a changed file in the current review scope
- **WHEN** the user runs `save problem diff`
- **THEN** cr writes `.cr/handoff/problem-diff.md`

#### Scenario: Refuse stale Source File problem diff

- **GIVEN** Source File is open
- **AND** the selected parsed problem no longer exactly matches the current source path and line
- **WHEN** the user runs `save problem diff`
- **THEN** cr does not write a file
- **AND** reports that there is no current source problem diff to save
