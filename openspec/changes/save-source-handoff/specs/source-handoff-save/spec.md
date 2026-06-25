# source-handoff-save Specification

## ADDED Requirements

### Requirement: Save current source context

The browser SHALL support saving the same Markdown handoff produced by `copy source`.

#### Scenario: Save selected Source File range

- **GIVEN** Source File has an active selected range
- **WHEN** the user runs `save source`
- **THEN** the selected source range is saved to `.cr/handoff/source.md`
- **AND** the current target line remains marked in the saved Markdown.

### Requirement: Save current source symbol

The browser SHALL support saving the same Markdown handoff produced by `copy source symbol`.

#### Scenario: Save File Detail source symbol

- **GIVEN** File Detail is focused on a changed source line inside a recognized symbol
- **WHEN** the user runs `save source symbol tmp/render.md`
- **THEN** the current symbol range is saved to `tmp/render.md`
- **AND** the browser remains on File Detail without mutating Source File selection.
