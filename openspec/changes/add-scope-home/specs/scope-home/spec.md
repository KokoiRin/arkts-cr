## ADDED Requirements

### Requirement: Browser provides a Review Scope Home
`cr browse` SHALL provide a first-level Review Scope Home page.

#### Scenario: Open Scope Home
- **WHEN** the user runs `scopes` or `scope`
- **THEN** the browser SHALL show a Scope Home page
- **AND** the page SHALL list worktree, staged, all local changes, recent commits, base ref, and explicit range entries

#### Scenario: Scope Home breadcrumb
- **GIVEN** Scope Home is visible
- **WHEN** the browser renders the context/status layer
- **THEN** it SHALL show `Scope: scope home`
- **AND** it SHALL NOT append `> Files`

#### Scenario: Select executable scope entry
- **GIVEN** Scope Home is visible
- **WHEN** the user selects an executable scope entry and presses Enter
- **THEN** the browser SHALL enter that Review Scope using the existing scope switching behavior

#### Scenario: Parameterized scope entries
- **GIVEN** Scope Home is visible
- **WHEN** the page renders base ref and explicit range entries
- **THEN** those entries SHALL explain the command form the user should type
- **AND** they SHALL NOT pretend to execute without a parameter
