# Source Symbol Selection

## ADDED Requirements

### Requirement: Source File can select the current symbol

The Source File page SHALL provide a command that selects the innermost
best-effort outline symbol containing the current source line.

#### Scenario: Select current method symbol

- **GIVEN** the browser is on Source File for a repo-local ArkTS/ETS/TS file
- **AND** the current line is inside a method parsed by the existing outline module
- **WHEN** the user runs `source select symbol`
- **THEN** the source selection SHALL become that method's start and end line
- **AND** the page SHALL redraw with the selected range visible
- **AND** the status SHALL include the selected symbol label and range

#### Scenario: No source page is open

- **GIVEN** the browser is not on Source File
- **WHEN** the user runs `source select symbol`
- **THEN** no source selection SHALL be changed
- **AND** the status SHALL tell the user to open a source file first

#### Scenario: No symbol contains the current line

- **GIVEN** the browser is on Source File
- **AND** no outline symbol contains the current source line
- **WHEN** the user runs `source select symbol`
- **THEN** no source selection SHALL be changed
- **AND** the status SHALL say no source symbol exists at the current line

### Requirement: Selected symbol range composes with copy source

The command SHALL reuse the existing Source File selection behavior so that a
subsequent `copy source` copies the selected symbol range with symbol metadata.

#### Scenario: Copy selected symbol

- **GIVEN** `source select symbol` selected the current method range
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL contain the selected range header
- **AND** it SHALL include the existing `Symbol: ...` metadata
- **AND** it SHALL not include lines outside the selected symbol range
