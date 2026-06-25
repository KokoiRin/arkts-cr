# source-file-problem-stepping Specification

## ADDED Requirements

### Requirement: Step between task problems from Source File

The browser SHALL let Source File users step to adjacent parsed task problems without returning to Task Output or Task Problems.

#### Scenario: Move to next problem source

- **GIVEN** Source File is showing the selected task problem source
- **WHEN** the user runs `next problem`
- **THEN** Source File updates to the next task problem path and line
- **AND** the page remains Source File.

#### Scenario: Move to previous problem source

- **GIVEN** Source File is showing a later task problem source
- **WHEN** the user runs `prev problem`
- **THEN** Source File updates to the previous task problem path and line
- **AND** the page remains Source File.

#### Scenario: Preserve page history

- **GIVEN** Source File was opened from Task Problems
- **WHEN** the user runs `next problem`
- **AND** then returns with `b`
- **THEN** the browser returns to Task Problems, not to the previous Source File problem.
