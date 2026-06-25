## ADDED Requirements

### Requirement: Source File Page selects a source range

The browser SHALL support a page-local line range selection in Source File Page.

#### Scenario: Select range

- **GIVEN** Source File Page is open for a repo-local source file
- **WHEN** the user runs `source select 4 8`
- **THEN** the page SHALL record the selected range `4-8`
- **AND** render the active selection in the Source File Page header and rows.

#### Scenario: Normalize reversed range

- **GIVEN** Source File Page is open
- **WHEN** the user runs `source select 8 4`
- **THEN** the page SHALL record the selected range `4-8`.

#### Scenario: Clear range

- **GIVEN** Source File Page has an active selected range
- **WHEN** the user runs `source clear selection`
- **THEN** the page SHALL clear the selected range.

### Requirement: Source range composes with source copy

The browser SHALL make `copy source` copy the active selected source range when
a Source File Page selection exists.

#### Scenario: Copy selected range

- **GIVEN** Source File Page has selected range `4-8`
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL include only source lines 4 through 8
- **AND** report that the selected source range was copied.

#### Scenario: Copy source context without selection

- **GIVEN** Source File Page has no selected range
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL keep the existing context-radius copy behavior.

### Requirement: Source range follows source page lifecycle

The browser SHALL treat range selection as Source File Page local state.

#### Scenario: New source file clears range

- **GIVEN** Source File Page has an active selected range
- **WHEN** another Source File Page is opened
- **THEN** the active selected range SHALL be cleared.

#### Scenario: Page history restores range

- **GIVEN** Source File Page has an active selected range
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active selected range SHALL be restored.
