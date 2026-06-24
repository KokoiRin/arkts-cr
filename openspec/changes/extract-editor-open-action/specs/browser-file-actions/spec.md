## MODIFIED Requirements

### Requirement: Browser opens selected files in an editor
The browser SHALL provide an `open` command that opens the selected changed file through the configured or platform editor command.

#### Scenario: Open selected file
- **WHEN** the user runs `open` with a changed file selected
- **THEN** the browser SHALL resolve the repository file path
- **AND** SHALL pass the first changed line when available
- **AND** SHALL launch the resolved editor command
- **AND** SHALL show feedback through the existing browser message/status area

#### Scenario: Open selected file with no file
- **WHEN** the user runs `open` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without changing page state

### Requirement: File actions module owns platform action details
The file actions module SHALL own command source resolution, platform fallback, template expansion, subprocess launch, and failure messages for open, copy, and reveal file actions.

#### Scenario: Resolve open source from file actions module
- **WHEN** open command diagnostics or execution need an editor command
- **THEN** the source SHALL be resolved through `cr.ui.file_actions`
- **AND** the source SHALL identify `cli`, `env`, `platform`, or `missing`
- **AND** browser action execution SHALL NOT duplicate editor fallback rules

### Requirement: Browser shows file action diagnostics
The browser SHALL provide a `file actions` command that explains the resolved source for open, copy, and reveal actions.

#### Scenario: Show unified action sources
- **WHEN** the user runs `file actions`
- **THEN** the browser SHALL show one diagnostic line for `open`
- **AND** SHALL show one diagnostic line for `copy`
- **AND** SHALL show one diagnostic line for `reveal`
- **AND** SHALL NOT execute any file action
