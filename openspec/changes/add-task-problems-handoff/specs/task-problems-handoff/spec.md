## ADDED Requirements

### Requirement: Browser copies selected task problem

The browser SHALL copy the selected Task Problems entry.

#### Scenario: Copy selected problem

- **GIVEN** Task Problems Page is visible with at least one problem selected
- **WHEN** the user runs `copy problem`
- **THEN** the browser SHALL copy text containing the selected problem location and output summary
- **AND** the browser SHALL keep the current page, selection, scroll, Review Scope, and task state unchanged

#### Scenario: Copy selected problem empty state

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `copy problem`
- **THEN** the browser SHALL report that no task problem can be copied
- **AND** it SHALL NOT launch the clipboard command

### Requirement: Browser copies all task problems

The browser SHALL copy every current Task Problems entry.

#### Scenario: Copy all problems

- **GIVEN** current task output has extracted problems
- **WHEN** the user runs `copy problems`
- **THEN** the browser SHALL copy a compact list containing every problem location and output summary in current output order

#### Scenario: Copy all problems empty state

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `copy problems`
- **THEN** the browser SHALL report that no task problems can be copied
- **AND** it SHALL NOT launch the clipboard command
