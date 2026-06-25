## ADDED Requirements

### Requirement: Browser saves focused problem context

The browser SHALL support saving the same focused Problem Context Markdown used
by `copy problem context`.

#### Scenario: Save selected task problem context

- **GIVEN** Task Problems has a selected problem with readable source
- **WHEN** the user runs `save problem context tmp/problem.md`
- **THEN** the browser SHALL write focused problem context Markdown to
  `tmp/problem.md`
- **AND** report the saved path.

#### Scenario: Save source page context

- **GIVEN** Source File Page is open for a readable source file
- **WHEN** the user runs `save problem context`
- **THEN** the browser SHALL write focused source/diff context to
  `.cr/handoff/problem-context.md`.

#### Scenario: No context available

- **GIVEN** neither Task Problems nor Source File Page has an active context
- **WHEN** the user runs `save problem context`
- **THEN** the browser SHALL report that there is no problem context to save.

### Requirement: Problem context save handles write failures

The browser SHALL report file-write failures without changing current page,
selection, task state, or review scope.

#### Scenario: Destination cannot be written

- **GIVEN** Problem Context Markdown can be generated
- **WHEN** saving to the requested destination fails
- **THEN** the browser SHALL report the destination path and the write error.
