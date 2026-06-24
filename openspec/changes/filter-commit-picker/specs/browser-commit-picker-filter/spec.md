## ADDED Requirements

### Requirement: Commit Picker filters recent commits
The browser SHALL support filtering loaded recent commits while Commit Picker is active.

#### Scenario: Filter commits from prompt
- **WHEN** the user enters a Commit Picker filter query
- **THEN** Commit Picker SHALL show only commits matching the query
- **AND** SHALL remain on Commit Picker

#### Scenario: Match commit fields
- **WHEN** a query matches a commit hash, authored date, subject, or displayed change summary
- **THEN** that commit SHALL remain visible in the filtered Commit Picker list

#### Scenario: Empty commit filter result
- **WHEN** no loaded recent commits match the query
- **THEN** Commit Picker SHALL show an empty filtered result message

### Requirement: Commit Picker filter is isolated
The Commit Picker filter SHALL be isolated from Changed Files and Command Palette filters.

#### Scenario: Clear active commit filter
- **WHEN** the user clears while Commit Picker is active
- **THEN** the Commit Picker filter SHALL be cleared
- **AND** the Changed Files path filter SHALL be preserved

#### Scenario: Select filtered commit
- **WHEN** the user selects a commit from filtered Commit Picker results
- **THEN** the browser SHALL enter the selected commit Review Scope
