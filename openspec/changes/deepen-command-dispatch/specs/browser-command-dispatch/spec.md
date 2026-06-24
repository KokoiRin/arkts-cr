## ADDED Requirements

### Requirement: Browser commands parse to stable actions
The browser SHALL parse command input into stable command actions before executing browser behavior.

#### Scenario: Alias commands map to the same action
- **WHEN** the parser receives aliases such as `q`, `quit`, or `exit`
- **THEN** it SHALL return the same quit action

#### Scenario: Parameter commands expose values
- **WHEN** the parser receives `base REF`, `range OLD..NEW`, `filter QUERY`, `/QUERY`, or a numeric choice
- **THEN** it SHALL return the matching action
- **AND** it SHALL expose the parsed value without requiring the execution layer to parse the raw string again

#### Scenario: Unknown commands remain explicit
- **WHEN** the parser receives an unsupported command
- **THEN** it SHALL return an unknown action
- **AND** the browser SHALL keep existing unknown-command feedback behavior

### Requirement: Existing browser command behavior remains stable
Introducing command dispatch SHALL preserve existing user-visible behavior.

#### Scenario: Existing commands still execute
- **WHEN** the user runs existing navigation, scope, task, filter, progress, file, and session commands
- **THEN** they SHALL behave as before command dispatch deepening

#### Scenario: Raw-key prompt sentinels remain browser-owned
- **WHEN** the command reader returns tick, eof, or interrupt sentinels
- **THEN** the browser loop SHALL keep existing lifecycle handling
- **AND** command dispatch SHALL NOT replace task-panel tick or clean-exit behavior
