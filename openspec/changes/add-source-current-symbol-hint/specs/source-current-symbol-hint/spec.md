## ADDED Requirements

### Requirement: Show current source symbol in Source File Page

The browser SHALL show a best-effort current symbol label in Source File Page when the target line belongs to a parsed source symbol.

#### Scenario: Show enclosing method label
- **GIVEN** Source File Page is showing a repo-local source file
- **AND** the target line is inside a parsed class method
- **WHEN** the page renders
- **THEN** the header SHALL include a readable symbol label for the enclosing method and container

#### Scenario: Omit missing symbol label
- **GIVEN** Source File Page is showing a source line outside parsed symbols
- **WHEN** the page renders
- **THEN** the header SHALL omit the symbol label rather than showing an unknown placeholder

### Requirement: Include current source symbol in source handoff

The browser SHALL include the current symbol label in copied source Markdown when a label is available.

#### Scenario: Copy source context with symbol
- **GIVEN** Source File Page target line belongs to a parsed symbol
- **WHEN** the user runs `copy source` without a selected range
- **THEN** the copied Markdown SHALL include the current symbol label
- **AND** it SHALL keep the existing source context line window unchanged

#### Scenario: Copy selected source range with symbol
- **GIVEN** Source File Page has an active source selection
- **AND** the target line belongs to a parsed symbol
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL include the current symbol label
- **AND** it SHALL keep the selected line range unchanged

### Requirement: Keep source symbol hints lightweight

Current source symbol hints MUST NOT introduce language-server dependencies, syntax-aware range expansion, source editing, workspace persistence, or Source File Page state fields.

#### Scenario: Symbol lookup is informational
- **GIVEN** source symbol parsing fails to identify an enclosing symbol
- **WHEN** Source File Page renders or copies source
- **THEN** source preview and copy behavior SHALL continue without a symbol label
