# source-file-copy-problem Specification

## ADDED Requirements

### Requirement: Copy current Source File task problem

The browser SHALL let Source File users copy the task problem represented by the current source target.

#### Scenario: Matching current problem

- **GIVEN** Source File is open at `src/Foo.ets:12`
- **AND** the selected parsed task problem is also `src/Foo.ets:12`
- **WHEN** the user runs `copy problem`
- **THEN** the browser copies that task problem handoff text.

#### Scenario: Stale selected problem

- **GIVEN** Source File is open at `src/Foo.ets:20`
- **AND** the selected parsed task problem is `src/Foo.ets:12`
- **WHEN** the user runs `copy problem`
- **THEN** the browser does not copy the stale selected problem
- **AND** reports that no current source problem is available.
