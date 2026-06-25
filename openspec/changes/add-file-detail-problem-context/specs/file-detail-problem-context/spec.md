# file-detail-problem-context Specification

## ADDED Requirements

### Requirement: File Detail Handoff Context

The browser SHALL allow users to copy or save an AI handoff context from File Detail using the currently rendered new-file line.

#### Scenario: Copy current File Detail line context

- **GIVEN** the browser is on File Detail for a changed file
- **AND** the current rendered row maps to a new-file source line
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text includes source context for that file and line
- **AND** the copied text includes the same-file diff context
- **AND** the browser remains on File Detail without changing scroll position

#### Scenario: Save current File Detail line context

- **GIVEN** the browser is on File Detail for a changed file
- **AND** the current rendered row maps to a new-file source line
- **WHEN** the user runs `save problem context PATH`
- **THEN** the saved text includes source context for that file and line
- **AND** the saved text includes the same-file diff context

#### Scenario: Deleted-only rows cannot produce source context

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row has no new-file source line
- **WHEN** the user runs `copy problem context` or `save problem context`
- **THEN** no handoff text is copied or saved
- **AND** the browser reports that there is no current new-file line in File Detail
