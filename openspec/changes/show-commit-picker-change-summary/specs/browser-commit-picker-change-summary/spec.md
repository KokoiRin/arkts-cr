## ADDED Requirements

### Requirement: Recent commit facts include change size
The system SHALL attach changed-file count and line churn totals to recent commit facts.

#### Scenario: Parse recent commit stats
- **WHEN** recent commits are loaded from Git
- **THEN** each returned commit fact SHALL include the number of changed files
- **AND** SHALL include added and deleted line totals when Git reports numeric stats

#### Scenario: Preserve commit identity
- **WHEN** recent commit facts include change size
- **THEN** each commit SHALL still include commit hash, parent hash, authored date, and subject

### Requirement: Commit Picker displays change size
The browser SHALL display each recent commit's change size in Commit Picker rows.

#### Scenario: Render commit row summary
- **WHEN** a Commit Picker row has changed-file count and line churn totals
- **THEN** the row SHALL include the file count and added/deleted totals

#### Scenario: Preserve commit picker navigation
- **WHEN** the user selects a commit with displayed change size
- **THEN** the browser SHALL enter the selected commit Review Scope using the same commit identity as before
