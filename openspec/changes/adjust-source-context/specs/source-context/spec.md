## ADDED Requirements

### Requirement: Source File Page copies configurable source context

The browser SHALL let users configure how many source lines around the current Source File Page target line are included by `copy source`.

#### Scenario: Default context remains unchanged

- **GIVEN** the user has not changed Source File Page context
- **WHEN** the user runs `copy source`
- **THEN** the copied snippet SHALL include up to three lines before and after the target line.

#### Scenario: User sets source context radius

- **GIVEN** the user is on Source File Page
- **WHEN** the user runs `source context 1`
- **THEN** future `copy source` output SHALL include up to one line before and after the target line.

#### Scenario: Source context is visible

- **GIVEN** Source File Page is rendered
- **WHEN** the source context radius is active
- **THEN** the page SHALL display the current context radius.

### Requirement: Source context radius is page-local browser state

The browser SHALL keep Source File Page context radius in page-local browser state.

#### Scenario: Page history restores source context

- **GIVEN** Source File Page has source context radius 8
- **WHEN** the user navigates away and then returns through page history
- **THEN** Source File Page SHALL restore source context radius 8.

#### Scenario: Opening a new source file resets context

- **GIVEN** Source File Page has source context radius 8
- **WHEN** the browser opens a different Source File Page from Task Problems
- **THEN** the new Source File Page SHALL use the default radius.
