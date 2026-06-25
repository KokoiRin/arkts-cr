## ADDED Requirements

### Requirement: Browser searches Source File Page

The browser SHALL search text within the current Source File Page.

#### Scenario: Find source text

- **GIVEN** Source File Page is visible with a readable source file
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL search source lines case-insensitively
- **AND** it SHALL move the Source File Page target line to the first matching source line
- **AND** it SHALL keep Review Scope, task state, and page history unchanged

#### Scenario: Missing source text

- **GIVEN** Source File Page is visible with a readable source file
- **WHEN** the user runs `find TEXT` with no matches
- **THEN** the browser SHALL report no matches
- **AND** it SHALL keep the current source target line and scroll unchanged

### Requirement: Browser repeats Source File Page search

The browser SHALL repeat Source File Page searches using page-local query state.

#### Scenario: Next source match

- **GIVEN** Source File Page has a previous non-empty source find query
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL move to the next matching source line with wraparound

#### Scenario: Previous source match

- **GIVEN** Source File Page has a previous non-empty source find query
- **WHEN** the user runs `prev match`
- **THEN** the browser SHALL move to the previous matching source line with wraparound

#### Scenario: No source query

- **GIVEN** Source File Page has no previous source find query
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL ask the user to enter text to find

### Requirement: Browser handles unreadable source find

The browser SHALL handle find on unreadable Source File Page state.

#### Scenario: Find unreadable source

- **GIVEN** Source File Page references a missing or unreadable file
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL report the source-file error without crashing
