## ADDED Requirements

### Requirement: Browser filters Changed Files by source
The browser SHALL support a source filter inside the current Changed Files view.

#### Scenario: Filter staged files
- **WHEN** the user runs `source staged`
- **THEN** visible changes SHALL include only files whose source is `staged`

#### Scenario: Filter unstaged files
- **WHEN** the user runs `source unstaged`
- **THEN** visible changes SHALL include only files whose source is `unstaged`

#### Scenario: Filter mixed files
- **WHEN** the user runs `source mixed`
- **THEN** visible changes SHALL include only files whose source is `mixed`

#### Scenario: Clear source filter
- **WHEN** the user runs `source all` or `source clear`
- **THEN** the source filter SHALL be cleared

### Requirement: Source filter composes with existing Changed Files filters
The source filter SHALL compose with path filtering and remaining-only filtering.

#### Scenario: Path and source filters combine
- **WHEN** a path filter and source filter are both active
- **THEN** visible changes SHALL match both filters

#### Scenario: Remaining-only and source filters combine
- **WHEN** remaining-only mode and source filter are both active
- **THEN** visible changes SHALL exclude seen paths and match the source filter

### Requirement: Browser displays active source filter
The browser SHALL show active source filter context in Changed Files rendering.

#### Scenario: Active source filter header
- **WHEN** a source filter is active
- **THEN** Changed Files output SHALL show the active source filter

### Requirement: Source filter uses existing command infrastructure
The browser SHALL expose source filtering through the parser, command palette, and action executor.

#### Scenario: Command palette lists source filter commands
- **WHEN** command palette entries are built
- **THEN** source filter commands SHALL be executable entries
