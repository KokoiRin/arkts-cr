## ADDED Requirements

### Requirement: Jump between visible Task Problems files

The browser SHALL let users move the Task Problems selection between file groups in the current visible Problems list.

#### Scenario: Jump to next file
- **GIVEN** Task Problems contains visible problems for `src/A.ets`, `src/B.ets`, and `src/C.ets`
- **AND** the selected problem is in `src/A.ets`
- **WHEN** the user runs `next problem file`
- **THEN** the selected problem SHALL move to the first visible problem in `src/B.ets`
- **AND** the browser SHALL preserve page, filters, sort, grouping, Review Scope, and task state

#### Scenario: Jump to previous file
- **GIVEN** Task Problems contains visible problems for `src/A.ets`, `src/B.ets`, and `src/C.ets`
- **AND** the selected problem is in `src/C.ets`
- **WHEN** the user runs `prev problem file`
- **THEN** the selected problem SHALL move to the first visible problem in `src/B.ets`

#### Scenario: Respect current visible filters
- **GIVEN** Task Problems has severity or text filters active
- **WHEN** the user runs `next problem file` or `prev problem file`
- **THEN** file jumps SHALL consider only the currently visible filtered problems

#### Scenario: Edge file keeps selection
- **GIVEN** the selected problem is already in the first or last visible file group
- **WHEN** the user runs the corresponding previous or next file jump command
- **THEN** the selected problem SHALL stay unchanged
- **AND** the browser SHALL show an explanatory status message
