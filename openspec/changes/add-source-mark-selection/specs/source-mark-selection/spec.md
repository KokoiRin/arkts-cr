## ADDED Requirements

### Requirement: Source File Page mark-based range selection
The browser SHALL let users select a Source File Page range by marking the
current source target line and selecting to the later current target line.

#### Scenario: Mark current line and select to another current line
- **GIVEN** the browser is on Source File Page at line 5
- **WHEN** the user runs `source mark`
- **AND** the current source target line later becomes 9
- **AND** the user runs `source select to`
- **THEN** the Source File Page selection SHALL be lines 5 through 9
- **AND** `copy source` SHALL keep using the selected range behavior

#### Scenario: Selection works regardless of direction
- **GIVEN** the browser is on Source File Page at line 9 with an active mark
  from line 5
- **WHEN** the current source target line later becomes 3
- **AND** the user runs `source select to`
- **THEN** the Source File Page selection SHALL be lines 3 through 5

#### Scenario: Mark is page-local
- **GIVEN** the browser has a source mark in Source File Page
- **WHEN** the user navigates away and returns through page history
- **THEN** the source mark SHALL be restored
- **WHEN** the user opens a different source file
- **THEN** the source mark SHALL be cleared
