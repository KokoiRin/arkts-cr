# file-detail-file-problems-handoff Specification

## ADDED Requirements

### Requirement: File Detail Current File Problems Handoff

The browser SHALL scope file-problem handoff commands to the current changed file when the user is in File Detail.

#### Scenario: Copy current File Detail file problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include entries for `src/Foo.ets` and `src/Bar.ets`
- **AND** the globally selected task problem belongs to `src/Bar.ets`
- **WHEN** the user runs `copy file problems`
- **THEN** the copied handoff includes only problems for `src/Foo.ets`.

#### Scenario: Save current File Detail file problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include entries for `src/Foo.ets`
- **WHEN** the user runs `save file problems tmp/foo.md`
- **THEN** the saved handoff contains problems for `src/Foo.ets`.

#### Scenario: Current File Detail file has no problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems contain no entries for `src/Foo.ets`
- **WHEN** the user runs `copy file problems`
- **THEN** the browser reports that the current file has no task problems.
