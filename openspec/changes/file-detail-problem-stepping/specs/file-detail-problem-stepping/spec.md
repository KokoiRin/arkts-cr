# file-detail-problem-stepping Specification

## ADDED Requirements

### Requirement: Step Current File Problems In File Detail

The browser SHALL let File Detail users step through parsed task problems for the current changed file without leaving File Detail.

#### Scenario: Next problem line is visible in current diff

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include multiple entries for `src/Foo.ets`
- **AND** the next selected problem line is visible in the rendered File Detail diff
- **WHEN** the user runs `next problem`
- **THEN** the browser keeps File Detail open
- **AND** updates the selected task problem
- **AND** scrolls to the rendered diff row for that problem line.

#### Scenario: Problem line is not visible in current diff

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** parsed task problems include an entry for `src/Foo.ets`
- **AND** that problem line is not visible in the rendered File Detail diff
- **WHEN** the user runs `next problem`
- **THEN** the browser keeps File Detail open
- **AND** updates the selected task problem
- **AND** reports that the problem line is not visible in the current diff.

#### Scenario: Current file has no task problems

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** no parsed task problem belongs to `src/Foo.ets`
- **WHEN** the user runs `next problem`
- **THEN** the browser keeps File Detail open
- **AND** reports that the current file has no task problems.
