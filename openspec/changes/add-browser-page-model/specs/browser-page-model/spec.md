## ADDED Requirements

### Requirement: Browser exposes an explicit page model
The browser SHALL expose explicit page names for the existing product pages.

#### Scenario: Page names exist
- **WHEN** maintainers inspect the browser page model
- **THEN** it SHALL include named pages for scope home, commit picker, changed files, file detail, and command palette
- **AND** those names SHALL map to the existing persisted/prompt string values

#### Scenario: Browser state owns current page
- **WHEN** a new browser state is created
- **THEN** its current page SHALL be Changed Files
- **AND** `mode` compatibility SHALL read and write the same current page

### Requirement: Existing browser behavior remains stable
Adding the page model SHALL preserve existing user-visible behavior.

#### Scenario: Existing prompts and persistence
- **WHEN** the browser renders prompts or saves workspace state
- **THEN** it SHALL keep the existing prompt strings and persisted mode values

#### Scenario: Existing navigation
- **WHEN** the user navigates between scope home, commit picker, changed files, file detail, and command palette
- **THEN** behavior SHALL remain the same as before the page model
