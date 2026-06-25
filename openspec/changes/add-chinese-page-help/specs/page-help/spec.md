## ADDED Requirements

### Requirement: Page-specific Chinese help
The interactive browser SHALL provide a Help page that explains the currently
active page in Chinese.

#### Scenario: Help opens for the current page
- **GIVEN** the browser is on Task Problems
- **WHEN** the user runs `help`
- **THEN** the browser shows the Help page
- **AND** the Help page describes Task Problems commands in Chinese

#### Scenario: Help preserves navigation
- **GIVEN** the browser opens Help from File Detail
- **WHEN** the user goes back
- **THEN** the browser returns to File Detail with its page state preserved

### Requirement: Chinese visible help surfaces
The interactive browser SHALL show Chinese labels and descriptions for the Help
page, contextual action bar, command palette, and command list.

#### Scenario: Command words remain executable
- **GIVEN** the command list is rendered in Chinese
- **THEN** executable command literals such as `build`, `problems group file`,
  and `copy source` remain unchanged
