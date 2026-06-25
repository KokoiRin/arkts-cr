## ADDED Requirements

### Requirement: Browser enriches task problems with diagnostics facts

The browser SHALL enrich extracted task problems with optional severity, code, and message facts when common task-output text contains them.

#### Scenario: Extract severity code and message after anchor

- **GIVEN** current task output contains `src/Foo.ets:12:3 error TS2322: bad call`
- **AND** `src/Foo.ets` exists inside the repo
- **WHEN** task problems are extracted
- **THEN** the extracted problem SHALL have severity `error`
- **AND** code `TS2322`
- **AND** message `bad call`.

#### Scenario: Preserve unknown diagnostics

- **GIVEN** current task output contains a repo-local `path:line[:column]` anchor but no recognized severity or code
- **WHEN** task problems are extracted
- **THEN** the problem SHALL still be returned
- **AND** its diagnostic facts SHALL be empty
- **AND** its raw summary SHALL be preserved.

### Requirement: Browser surfaces diagnostics facts in Problems UI and handoff

The browser SHALL surface extracted diagnostics facts in the Problems page and copy handoff text.

#### Scenario: Render compact diagnostic label

- **GIVEN** Task Problems page has a problem with severity `error` and code `TS2322`
- **WHEN** the page renders rows
- **THEN** the row SHALL include a compact `ERROR TS2322` label.

#### Scenario: Copy diagnostic facts

- **GIVEN** a task problem has severity, code, and message
- **WHEN** the user copies that problem
- **THEN** the copied handoff text SHALL include the location plus severity, code, and message facts.
