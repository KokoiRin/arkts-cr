## ADDED Requirements

### Requirement: Browser workspace persistence module owns state file I/O
The browser SHALL use a dedicated UI module for browser workspace persistence file paths, version wrapping, JSON read/write, load validation, and save/restore eligibility decisions.

#### Scenario: Save workspace state through persistence module
- **WHEN** the browser saves default workspace state
- **THEN** the persistence module SHALL write `.git/cr/browse-state.json`
- **AND** SHALL include schema version `1`
- **AND** SHALL preserve the existing workspace state fields
- **AND** SHALL NOT persist task runtime or task history

#### Scenario: Load valid workspace state
- **WHEN** the persistence module loads a valid state file
- **THEN** it SHALL return the persisted state mapping
- **AND** SHALL reject files with invalid JSON, non-object roots, wrong versions, or missing scope objects

#### Scenario: Preserve restore and save eligibility
- **WHEN** a browse session uses explicit staged/all/base/range/untracked/path arguments
- **THEN** default workspace restore SHALL NOT run
- **AND** save-on-exit SHALL NOT write state for explicit path arguments

#### Scenario: Browser delegates persistence without changing behavior
- **WHEN** existing browser wrapper functions are called
- **THEN** they SHALL preserve current behavior
- **AND** their implementation SHALL delegate file I/O and persistence schema handling to the workspace persistence module
