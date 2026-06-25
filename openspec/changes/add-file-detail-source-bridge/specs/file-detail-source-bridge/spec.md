# File Detail Source Bridge

## ADDED Requirements

### Requirement: File Detail can open Source File at current new line

The File Detail page SHALL provide a command that opens the Source File page at
the current rendered new-file line.

#### Scenario: View source from current diff row

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL open Source File for the current changed file
- **AND** the Source File target line SHALL be the mapped new-file line
- **AND** Back SHALL return to the same File Detail scroll

#### Scenario: Current row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row is a deleted-only row or another row without a new-file line
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL remain on File Detail
- **AND** the status SHALL say there is no current new-file line

#### Scenario: Not on File Detail

- **GIVEN** the browser is not on File Detail
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL stay on the current page
- **AND** the status SHALL tell the user to open a file detail first
