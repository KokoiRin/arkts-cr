## ADDED Requirements

### Requirement: Copy visible same-file task problems
The browser SHALL let users copy all currently visible Task Problems that share
the selected problem's file path.

#### Scenario: Copy problems for the selected file
- **GIVEN** Task Problems contains visible problems for `src/A.ets` and
  `src/B.ets`
- **AND** the selected problem is in `src/A.ets`
- **WHEN** the user runs `copy file problems`
- **THEN** the copied Markdown SHALL include only visible problems from
  `src/A.ets`
- **AND** the browser SHALL preserve page, selection, filters, sort, grouping,
  Review Scope, and task state

#### Scenario: Respect current visible filters
- **GIVEN** Task Problems has severity or text filters active
- **WHEN** the user runs `copy file problems`
- **THEN** the copied Markdown SHALL use only the currently visible filtered
  problems for the selected file

#### Scenario: Empty Problems list
- **GIVEN** no Task Problems are currently visible
- **WHEN** the user runs `copy file problems`
- **THEN** the browser SHALL report that there are no task problems to copy
