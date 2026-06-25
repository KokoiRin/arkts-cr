# Copy Source Symbol

## ADDED Requirements

### Requirement: Source File can copy current symbol

Source File SHALL provide `copy source symbol` to copy the innermost best-effort
symbol range containing the current source line.

#### Scenario: Copy current Source File method

- **GIVEN** the browser is on Source File
- **AND** the current line is inside a parsed method
- **WHEN** the user runs `copy source symbol`
- **THEN** copied Markdown SHALL contain that method's source range
- **AND** it SHALL include `Symbol: ...` metadata
- **AND** it SHALL not change the current source selection

### Requirement: File Detail can copy current row symbol

File Detail SHALL provide `copy source symbol` to copy the innermost best-effort
symbol range containing the current rendered new-file line.

#### Scenario: Copy current File Detail method

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line inside a parsed method
- **WHEN** the user runs `copy source symbol`
- **THEN** copied Markdown SHALL contain that method's source range
- **AND** the browser SHALL remain on File Detail

#### Scenario: Current row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row has no new-file line
- **WHEN** the user runs `copy source symbol`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say there is no current new-file line

### Requirement: Missing symbol is reported

When no best-effort source symbol contains the target line, the command SHALL
not copy text and SHALL tell the user no source symbol exists at the current line.

#### Scenario: Copy symbol outside any parsed symbol

- **GIVEN** the browser is on Source File
- **AND** the current line is not inside any parsed symbol
- **WHEN** the user runs `copy source symbol`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say no source symbol exists at the current line
