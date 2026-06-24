## ADDED Requirements

### Requirement: Command palette lists executable commands
`cr browse` SHALL provide an executable command palette in commands mode.

#### Scenario: Open command palette
- **WHEN** the user enters `commands`, `cmds`, or `help commands`
- **THEN** the browser SHALL enter commands mode
- **AND** it SHALL show commands that can be executed directly from the palette

#### Scenario: Non-executable command templates are excluded
- **WHEN** the browser renders the executable command palette
- **THEN** parameter templates such as `base REF` and `range OLD..NEW` SHALL NOT be executable palette rows
- **AND** users SHALL still be able to type those commands through the normal command prompt

### Requirement: Command palette supports keyboard selection
`cr browse` SHALL let raw-key users move within the command palette without changing the selected review file.

#### Scenario: Move selected palette command
- **GIVEN** commands mode is active
- **WHEN** the user presses ↑/↓ or j/k
- **THEN** the selected palette command SHALL move within the executable command list
- **AND** the selected changed file SHALL remain unchanged

#### Scenario: Return to file list
- **GIVEN** commands mode is active
- **WHEN** the user presses b or ←
- **THEN** the browser SHALL return to list mode
- **AND** the selected changed file SHALL remain unchanged

### Requirement: Command palette executes selected commands
`cr browse` SHALL execute the selected palette command when users press Enter in commands mode.

#### Scenario: Execute selected command
- **GIVEN** commands mode is active
- **AND** a palette command is selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute that command through the same command handling path as typed commands

#### Scenario: Enter does not open a file from commands mode
- **GIVEN** commands mode is active
- **AND** the review has visible changed files
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute the selected palette command
- **AND** it SHALL NOT open the selected changed file unless the selected palette command is an explicit file-opening command
