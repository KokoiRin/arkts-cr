## ADDED Requirements

### Requirement: Browser copies selected file path
The browser SHALL provide a command action that copies the selected changed file's repository-relative path.

#### Scenario: Copy selected path
- **WHEN** the user runs `copy path` with a changed file selected
- **THEN** the browser SHALL copy that file's repo-relative path
- **AND** show feedback through the existing browser message/status area

#### Scenario: Copy path with no file
- **WHEN** the user runs `copy path` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without changing page state

### Requirement: Browser copies selected file anchor
The browser SHALL provide a command action that copies a review anchor for the selected changed file.

#### Scenario: Copy selected anchor with first changed line
- **WHEN** the selected file has a first changed line
- **THEN** the copied anchor SHALL be `path:line`

#### Scenario: Copy selected anchor without first changed line
- **WHEN** the selected file has no first changed line
- **THEN** the copied anchor SHALL fall back to the repo-relative path

### Requirement: Browser reveals selected file
The browser SHALL provide a command action that reveals the selected changed file in the OS file browser when supported.

#### Scenario: Reveal selected file
- **WHEN** the user runs `reveal` with a changed file selected
- **THEN** the browser SHALL launch the supported OS reveal command for that repository file
- **AND** show feedback through the existing browser message/status area

### Requirement: File actions use browser command infrastructure
The browser SHALL expose file actions through the existing parser, command palette, and action executor.

#### Scenario: Command palette lists file actions
- **WHEN** the command palette is rendered
- **THEN** `copy path`, `copy anchor`, and `reveal` SHALL appear as executable file commands
