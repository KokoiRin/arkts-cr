# source-file-problem-header Specification

## ADDED Requirements

### Requirement: Show current task problem on Source File

The browser SHALL show a compact current task problem label on Source File when the current source target corresponds to the selected parsed task problem.

#### Scenario: Matching task problem

- **GIVEN** Source File is open at `src/Foo.ets:12`
- **AND** the selected parsed task problem is also `src/Foo.ets:12`
- **WHEN** the Source File page renders
- **THEN** the header includes a compact task problem label.

#### Scenario: Stale selected problem

- **GIVEN** Source File is open at `src/Foo.ets:20`
- **AND** the selected parsed task problem is `src/Foo.ets:12`
- **WHEN** the Source File page renders
- **THEN** the header does not show that stale task problem label.
