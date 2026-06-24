## ADDED Requirements

### Requirement: Browser runs test and lint tasks
`cr browse` SHALL support configured test and lint commands through the same background task panel used for build tasks.

#### Scenario: Start test task
- **GIVEN** a test command is configured
- **WHEN** the user enters `test` or `tests`
- **THEN** the browser SHALL start that command as the current background task
- **AND** the task panel SHALL identify it as a test task

#### Scenario: Start lint task
- **GIVEN** a lint command is configured
- **WHEN** the user enters `lint`
- **THEN** the browser SHALL start that command as the current background task
- **AND** the task panel SHALL identify it as a lint task

#### Scenario: Missing task command
- **GIVEN** no command is configured for the requested task kind
- **WHEN** the user starts that task
- **THEN** the task panel SHALL show a readable configuration message
- **AND** it SHALL NOT start a guessed command

### Requirement: Current task controls are task-kind aware
The browser SHALL apply stop and rerun controls to the current or most recent task kind.

#### Scenario: Stop current task
- **GIVEN** a build, test, or lint task is running
- **WHEN** the user enters `stop` or `cancel`
- **THEN** the browser SHALL stop the running task process group
- **AND** the panel SHALL describe the stopped task kind

#### Scenario: Rerun recent task
- **GIVEN** a test or lint task was the most recently started task
- **WHEN** the user enters `rerun`
- **THEN** the browser SHALL run the same task kind again

### Requirement: Task commands are discoverable
The command help and command palette SHALL expose build, test, lint, stop, and rerun commands.

#### Scenario: Open command palette
- **WHEN** the user opens the command palette
- **THEN** executable entries SHALL include build, test, lint, stop, and rerun task actions
