## ADDED Requirements

### Requirement: Local changes expose source facts
The system SHALL annotate local changed-file facts with their current Git index/worktree source.

#### Scenario: Staged scope source
- **WHEN** changed files are loaded for staged/index review
- **THEN** each returned tracked file change SHALL have source `staged`

#### Scenario: Worktree scope source
- **WHEN** changed files are loaded for unstaged worktree review
- **THEN** each returned tracked file change SHALL have source `unstaged`

#### Scenario: All-local mixed source
- **WHEN** changed files are loaded for all local changes
- **AND** a path has both staged and unstaged changes
- **THEN** that file change SHALL have source `mixed`

#### Scenario: Read-only comparison scope
- **WHEN** changed files are loaded for `base`, `range`, or selected commit comparison
- **THEN** returned file changes SHALL NOT have local source badges

### Requirement: Browser renders change source badges
The browser SHALL show local change source badges in Changed Files rows.

#### Scenario: Changed Files row with source
- **WHEN** a visible changed file has source `staged`, `unstaged`, or `mixed`
- **THEN** the Changed Files row SHALL include that source badge
- **AND** preserve progress, note, status, counts, and tree label rendering

#### Scenario: Changed Files row without source
- **WHEN** a visible changed file has no local source
- **THEN** the Changed Files row SHALL omit the source badge
