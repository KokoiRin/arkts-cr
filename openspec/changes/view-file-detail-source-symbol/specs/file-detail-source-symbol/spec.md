# file-detail-source-symbol Specification

## ADDED Requirements

### Requirement: Open current File Detail source symbol

The browser SHALL let File Detail users open the current new-file source line in Source File and select the enclosing lightweight source symbol.

#### Scenario: Current diff row is inside a source symbol

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** the current rendered row maps to new-file line 12
- **AND** line 12 is inside a recognized function or method
- **WHEN** the user runs `view source symbol`
- **THEN** the browser opens Source File for `src/Foo.ets` at line 12
- **AND** selects the recognized enclosing symbol range.

#### Scenario: Current diff row has no new-file line

- **GIVEN** File Detail is open for a deleted-only or metadata row
- **WHEN** the user runs `view source symbol`
- **THEN** the browser stays on File Detail
- **AND** reports that there is no current new-file line.

#### Scenario: Current source line has no recognized symbol

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** the current rendered row maps to a new-file line
- **AND** that source line is not inside a recognized lightweight source symbol
- **WHEN** the user runs `view source symbol`
- **THEN** the browser opens Source File at that line
- **AND** reports that no source symbol is available without creating a fake selection.
