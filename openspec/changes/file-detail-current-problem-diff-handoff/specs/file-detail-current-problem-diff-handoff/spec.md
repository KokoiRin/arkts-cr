# file-detail-current-problem-diff-handoff Specification

## ADDED Requirements

### Requirement: Copy or save current File Detail row problem diff

The browser SHALL let File Detail users copy or save the changed-file diff for the task problem that exactly matches the current changed file and rendered new-file line.

#### Scenario: Current diff row problem diff is copied

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **AND** the globally selected task problem points at another file
- **WHEN** the user runs `copy problem diff`
- **THEN** the browser copies the diff for `src/One.ets`
- **AND** it does not copy the globally selected problem's file diff.

#### Scenario: Current diff row problem diff is saved

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem diff tmp/problem-diff.md`
- **THEN** the browser writes the changed-file diff for `src/One.ets`.

#### Scenario: Current diff row has no matching problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem diff`
- **THEN** the browser refuses the command
- **AND** it does not fall back to any globally selected task problem.
