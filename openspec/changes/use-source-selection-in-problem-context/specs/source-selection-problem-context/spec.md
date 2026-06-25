## ADDED Requirements

### Requirement: Source File problem context uses selected source ranges

The browser SHALL use the active Source File selected range when generating
Problem Context Markdown directly from Source File Page.

#### Scenario: Copy selected Source File problem context

- **GIVEN** Source File Page is open with an active selected source range
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the selected source range
- **AND** it SHALL NOT include source lines outside that selected range.

#### Scenario: Save selected Source File problem context

- **GIVEN** Source File Page is open with an active selected source range
- **WHEN** the user runs `save problem context`
- **THEN** the saved Markdown SHALL include the selected source range.

### Requirement: Source File problem context preserves line context fallback

The browser SHALL keep the existing Source File line-context behavior when no
source range is selected.

#### Scenario: Copy unselected Source File problem context

- **GIVEN** Source File Page is open without a selected source range
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the configured source context radius
  around the current source line.
