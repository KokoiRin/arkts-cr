## ADDED Requirements

### Requirement: Browser command list entry points
`cr browse` SHALL provide in-session entry points for users to discover command prompt commands.

#### Scenario: Open command list from line mode
- **WHEN** the browser receives `commands`, `cmds`, or `help commands`
- **THEN** the browser SHALL show a command list
- **AND** the session SHALL remain open

#### Scenario: Open command list from raw command prompt
- **WHEN** the browser is in raw-key mode and the user opens `:` command input
- **AND** the user submits empty input or `?`
- **THEN** the browser SHALL show a command list

### Requirement: Browser command list content
The command list SHALL group available browser commands by purpose.

#### Scenario: Show grouped commands
- **WHEN** the command list is shown
- **THEN** it SHALL include navigation commands
- **AND** it SHALL include review scope commands
- **AND** it SHALL include build task commands
- **AND** it SHALL include file/session commands

#### Scenario: Return from command list
- **WHEN** the command list is shown and the user enters `b` or `back`
- **THEN** the browser SHALL return to the changed-file list
- **AND** active build task output SHALL remain available in the bottom task panel
