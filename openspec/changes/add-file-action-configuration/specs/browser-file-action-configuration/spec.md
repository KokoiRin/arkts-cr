## ADDED Requirements

### Requirement: Browser supports configured copy command
The browser SHALL allow users to configure the command used by `copy path` and `copy anchor`.

#### Scenario: Copy command from CLI argument
- **WHEN** the user provides `--copy-cmd`
- **THEN** `copy path` and `copy anchor` SHALL use that command
- **AND** SHALL provide the copied text to the command

#### Scenario: Copy command from environment
- **WHEN** `CR_COPY_CMD` is set and no CLI copy command is provided
- **THEN** copy actions SHALL use `CR_COPY_CMD`

### Requirement: Browser supports configured reveal command
The browser SHALL allow users to configure the command used by `reveal`.

#### Scenario: Reveal command from CLI argument
- **WHEN** the user provides `--reveal-cmd`
- **THEN** `reveal` SHALL use that command for the selected repository file

#### Scenario: Reveal command from environment
- **WHEN** `CR_REVEAL_CMD` is set and no CLI reveal command is provided
- **THEN** reveal SHALL use `CR_REVEAL_CMD`

### Requirement: Built-in file action fallbacks remain
The browser SHALL preserve built-in platform copy and reveal fallbacks when no configured command is present.

#### Scenario: No configured file action command
- **WHEN** no CLI argument or environment variable is set for a file action
- **THEN** the existing platform fallback behavior SHALL remain available

### Requirement: File action configuration stays behind file action helpers
The browser SHALL keep command-template parsing and subprocess execution inside `cr.ui.file_actions`.

#### Scenario: Browser executes configured file action
- **WHEN** the browser executes copy or reveal
- **THEN** browser action execution SHALL pass configuration to the file action helper without parsing the template itself
