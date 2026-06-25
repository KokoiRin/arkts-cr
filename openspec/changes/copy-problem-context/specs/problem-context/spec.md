## ADDED Requirements

### Requirement: Browser copies selected problem context

The browser SHALL copy a focused Markdown context package for the currently selected task problem.

#### Scenario: Copy context from Task Problems

- **GIVEN** Task Problems has a selected problem whose source file can be read
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include the selected problem facts
- **AND** it SHALL include source context around the problem line
- **AND** it SHALL include same-file diff context when the file is changed in the current Review Scope.

#### Scenario: Copy context without matching diff

- **GIVEN** Task Problems has a selected problem whose file is not changed in the current Review Scope
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include problem and source context
- **AND** it SHALL state that there is no diff in the current review scope.

### Requirement: Browser copies source page context

The browser SHALL copy a focused Markdown context package from Source File Page.

#### Scenario: Copy context from Source File Page

- **GIVEN** Source File Page is open on a repo-local source file
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include the source target anchor
- **AND** it SHALL include source context using the active source context radius
- **AND** it SHALL include same-file diff context when available.

### Requirement: Problem context command is surfaced in TUI commands

The browser SHALL expose `copy problem context` through command parsing, command catalog, and contextual action bars for Task Problems and Source File Page.

#### Scenario: Command is visible

- **GIVEN** the user opens command help or a relevant page action bar
- **WHEN** the browser renders commands
- **THEN** `copy problem context` SHALL be discoverable.
