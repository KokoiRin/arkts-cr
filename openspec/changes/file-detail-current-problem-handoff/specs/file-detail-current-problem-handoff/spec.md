# file-detail-current-problem-handoff Specification

## ADDED Requirements

### Requirement: Copy or save current File Detail row problem

The browser SHALL let File Detail users copy or save the single task problem that exactly matches the current changed file and rendered new-file line.

#### Scenario: Current diff row matches a task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **AND** the globally selected task problem points at another file
- **WHEN** the user runs `copy problem`
- **THEN** the browser copies the `src/One.ets:4` problem
- **AND** it does not copy the globally selected problem.

#### Scenario: Save current diff row problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem tmp/problem.md`
- **THEN** the browser writes a single-problem handoff file for `src/One.ets:4`.

#### Scenario: Current diff row has no matching problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem`
- **THEN** the browser refuses the command
- **AND** it does not fall back to any globally selected task problem.
