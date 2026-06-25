# source-file-current-problem-context Specification

## ADDED Requirements

### Requirement: Enrich Source File problem context with current task problem

The browser SHALL include problem text and nearby task output in Source File problem context handoff when the current source line exactly matches the selected parsed task problem.

#### Scenario: Current Source File line matches a task problem

- **GIVEN** Source File is open for `src/Foo.ets` at line 5
- **AND** the selected task problem is exactly `src/Foo.ets:5`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes a `Problem` section
- **AND** includes a nearby `Task Output` excerpt
- **AND** includes the current source context and changed-file diff.

#### Scenario: Source selection is active

- **GIVEN** Source File is open for `src/Foo.ets` at line 5
- **AND** the selected task problem is exactly `src/Foo.ets:5`
- **AND** a source range is selected
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes the selected source range
- **AND** still includes the current problem and task output excerpt.

#### Scenario: Current Source File line has no matching problem

- **GIVEN** Source File is open for `src/Foo.ets` at line 8
- **AND** the selected task problem points at another line or file
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context still includes source and diff
- **AND** it does not include the stale selected task problem.
