## ADDED Requirements

### Requirement: Save browser workspace on exit
`cr browse` SHALL save the current browser review workspace on clean session exit.

#### Scenario: Save changed-file workspace
- **WHEN** a user exits `cr browse`
- **THEN** the browser SHALL save the active review scope
- **AND** it SHALL save the active file filter
- **AND** it SHALL save the selected changed file path and selected index
- **AND** it SHALL save whether the user was on the file list or file diff layer

### Requirement: Restore default browser workspace
Default `cr browse` SHALL restore the saved browser review workspace when no explicit scope or pathspec overrides are provided.

#### Scenario: Restore selected filtered file
- **GIVEN** a saved browser workspace with a filter and selected path
- **WHEN** the user starts default `cr browse`
- **THEN** the browser SHALL restore the saved scope before loading changes
- **AND** it SHALL restore the filter
- **AND** it SHALL select the saved path when that path is still visible
- **AND** it SHALL restore the saved list or file layer

#### Scenario: Saved path is no longer visible
- **GIVEN** a saved selected path that is no longer present in current changes
- **WHEN** the user starts default `cr browse`
- **THEN** the browser SHALL fall back to the saved index
- **AND** it SHALL clamp the selection to the current visible changes
- **AND** it SHALL NOT crash

### Requirement: Explicit CLI intent wins
Saved browser workspace SHALL NOT override explicit CLI scope or pathspec input.

#### Scenario: User passes explicit scope
- **GIVEN** a saved browser workspace
- **WHEN** the user starts `cr browse --staged`, `--all`, `--base REF`, `--range OLD..NEW`, or `--untracked`
- **THEN** the browser SHALL use the CLI-provided scope
- **AND** it SHALL ignore the saved scope for that session

#### Scenario: User passes pathspec
- **GIVEN** a saved browser workspace
- **WHEN** the user starts `cr browse src/pages`
- **THEN** the browser SHALL use the CLI-provided pathspec
- **AND** it SHALL ignore the saved filter and selected path for that session

### Requirement: Invalid saved workspace is ignored
`cr browse` SHALL ignore missing, unreadable, malformed, or unsupported workspace state files without failing startup.

#### Scenario: Saved workspace file is malformed
- **GIVEN** the saved browser workspace file contains malformed JSON
- **WHEN** the user starts default `cr browse`
- **THEN** the browser SHALL ignore the saved file
- **AND** it SHALL continue with normal default startup
