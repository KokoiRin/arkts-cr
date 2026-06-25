## ADDED Requirements

### Requirement: Browser copies Source File Page source context

The browser SHALL copy a compact source context snippet for the current Source File Page target line.

#### Scenario: Copy source context

- **GIVEN** Source File Page is visible for `src/Foo.ets`
- **AND** its target line is `20`
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL copy Markdown headed by `src/Foo.ets:20`
- **AND** the copied code block SHALL include nearby source lines with line numbers
- **AND** the target line SHALL be marked.

#### Scenario: Empty source state

- **GIVEN** Source File Page is visible without a source path
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL report that there is no source file to copy
- **AND** it SHALL not call the clipboard command.

### Requirement: Browser advertises source context copy

The browser SHALL expose `copy source` in command help and Source File Page actions.

#### Scenario: Source File Page action bar

- **GIVEN** Source File Page is visible
- **WHEN** the contextual action bar renders
- **THEN** it SHALL include `copy source`.
