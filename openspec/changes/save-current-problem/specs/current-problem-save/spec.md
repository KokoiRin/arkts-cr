## ADDED Requirements

### Requirement: Save Current Task Problem

The browser SHALL support saving the current single task problem as Markdown.

#### Scenario: Save selected problem from Task Problems

- **GIVEN** Task Problems has visible parsed problems
- **AND** one problem is selected
- **WHEN** the user runs `save problem`
- **THEN** cr writes that problem to `.cr/handoff/task-problem.md`
- **AND** the browser stays on Task Problems with selection preserved

#### Scenario: Save selected problem to requested path

- **GIVEN** a current task problem exists
- **WHEN** the user runs `save problem tmp/problem.md`
- **THEN** cr writes that problem to `tmp/problem.md`

#### Scenario: Refuse stale Source File problem

- **GIVEN** Source File is open
- **AND** the selected parsed problem no longer exactly matches the current source path and line
- **WHEN** the user runs `save problem`
- **THEN** cr does not write a file
- **AND** reports that there is no current source problem to save
