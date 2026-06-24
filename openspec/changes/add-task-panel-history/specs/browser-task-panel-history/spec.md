## ADDED Requirements

### Requirement: Task panel records completed build tasks
`cr browse` SHALL keep a compact in-session history of completed background build tasks.

#### Scenario: Build completes
- **WHEN** a background build reaches a terminal state
- **THEN** the browser SHALL append one task history record
- **AND** the record SHALL include the task kind, command, status, and return code when available

#### Scenario: Build is polled repeatedly after completion
- **GIVEN** a completed build has already been recorded
- **WHEN** the browser polls again
- **THEN** it SHALL NOT append a duplicate history record for the same build

### Requirement: Task panel renders recent task history
`cr browse` SHALL show recent task results in the bottom task panel.

#### Scenario: Render build panel with history
- **GIVEN** one or more task history records exist
- **WHEN** the build panel is rendered
- **THEN** it SHALL show a compact recent-task summary
- **AND** it SHALL still show the current build status and latest log lines

#### Scenario: Rerun build after completion
- **GIVEN** a build has completed and been recorded
- **WHEN** the user starts another build
- **THEN** the build panel SHALL show the new current build
- **AND** it SHALL retain the previous build in recent task history for the session

### Requirement: Task history stays session-local
Task history SHALL NOT be persisted to browser workspace state.

#### Scenario: Save browser workspace
- **WHEN** browser workspace state is saved
- **THEN** task history SHALL NOT be written to `.git/cr/browse-state.json`
