# task-problems-list-save Specification

## ADDED Requirements

### Requirement: Save current Task Problems list

The browser SHALL support saving the current visible Task Problems list as Markdown.

#### Scenario: Save default problems list

- **GIVEN** the current task output contains visible problems
- **WHEN** the user runs `save problems`
- **THEN** the current visible problem list is saved to `.cr/handoff/task-problems.md`
- **AND** the browser reports the number of saved problems.

### Requirement: Save selected-file Task Problems list

The browser SHALL support saving visible Task Problems for the selected problem's file.

#### Scenario: Save file-specific problems list

- **GIVEN** the current visible problem list contains multiple files
- **AND** the selected problem belongs to `src/Two.ets`
- **WHEN** the user runs `save file problems tmp/two-problems.md`
- **THEN** only visible problems from `src/Two.ets` are saved to `tmp/two-problems.md`
- **AND** the browser reports the number of saved problems and selected path.
