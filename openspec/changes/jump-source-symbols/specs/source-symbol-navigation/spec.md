## ADDED Requirements

### Requirement: Source File supports adjacent symbol navigation

The browser SHALL support jumping to adjacent recognized source symbols from
Source File Page.

#### Scenario: Jump to next symbol

- **GIVEN** Source File Page is open on a line before another recognized symbol
- **WHEN** the user runs `next symbol`
- **THEN** the current source line SHALL move to the next symbol start line
- **AND** the page SHALL remain Source File Page.

#### Scenario: Jump to previous symbol

- **GIVEN** Source File Page is open on a line after a recognized symbol
- **WHEN** the user runs `prev symbol`
- **THEN** the current source line SHALL move to the previous symbol start line
- **AND** the page SHALL remain Source File Page.

### Requirement: Source symbol navigation handles empty and boundary states

The browser SHALL report clear status messages without changing the current
source line when adjacent source-symbol navigation cannot move.

#### Scenario: No next symbol

- **GIVEN** Source File Page is open at or after the final recognized symbol
- **WHEN** the user runs `next symbol`
- **THEN** the browser SHALL report that it is already at the last symbol
- **AND** preserve the current source line.

#### Scenario: No source symbols

- **GIVEN** Source File Page is open for a readable file with no recognized
  symbols
- **WHEN** the user runs `next symbol`
- **THEN** the browser SHALL report that no source symbols were found
- **AND** preserve the current source line.
