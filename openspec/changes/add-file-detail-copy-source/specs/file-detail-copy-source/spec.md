# File Detail Copy Source

## ADDED Requirements

### Requirement: File Detail can copy source context

The File Detail page SHALL allow `copy source` to copy Source File-style
Markdown for the current rendered new-file line.

#### Scenario: Copy source from current diff row

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line
- **WHEN** the user runs `copy source`
- **THEN** copied Markdown SHALL be anchored to the current changed file and mapped line
- **AND** it SHALL include source context around that line
- **AND** it SHALL include best-effort symbol metadata when available
- **AND** the browser SHALL remain on File Detail

#### Scenario: Current diff row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row has no new-file line
- **WHEN** the user runs `copy source`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say there is no current new-file line

### Requirement: Source File copy source remains unchanged

The existing Source File `copy source` behavior SHALL continue to copy selected
ranges or target-line context as before.

#### Scenario: Copy source from Source File

- **GIVEN** the browser is on Source File
- **WHEN** the user runs `copy source`
- **THEN** the existing Source File copy behavior SHALL be preserved
