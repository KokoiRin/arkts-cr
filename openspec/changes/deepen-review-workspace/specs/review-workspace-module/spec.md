## ADDED Requirements

### Requirement: Review workspace owns active scope and changed files
The browser SHALL use a dedicated review workspace module to own active Review Scope state and changed-file loading behavior.

#### Scenario: Workspace loads current scope
- **WHEN** a review workspace is created from the current browser arguments
- **THEN** it SHALL load sorted changed files through the existing review selection path
- **AND** it SHALL expose the same changed files to the browser UI

#### Scenario: Workspace switches local scopes
- **WHEN** the browser switches to worktree, staged, all local changes, base, or range scope
- **THEN** the workspace SHALL update the active scope
- **AND** it SHALL reload changed files
- **AND** it SHALL reset selected commit, previous scope, filter, selection, and scroll state as existing behavior does

#### Scenario: Workspace selects a commit scope
- **WHEN** the browser selects a recent commit
- **THEN** the workspace SHALL capture the previous scope if needed
- **AND** it SHALL switch active scope to that commit's ref range
- **AND** it SHALL reload changed files and return to Changed Files

### Requirement: Review workspace preserves existing persistence behavior
Introducing the review workspace module SHALL preserve browser workspace state compatibility.

#### Scenario: Workspace state is saved
- **WHEN** the browser saves workspace state on clean exit
- **THEN** the saved JSON SHALL keep the same version, scope, filter, selected path/index, mode, seen paths, and remaining-only fields

#### Scenario: Workspace state is restored
- **WHEN** compatible workspace state exists and no explicit scope override is passed
- **THEN** the browser SHALL restore the same scope, filter, selected file, progress markers, and list/file page as before

### Requirement: UI-only browser state remains outside review workspace
The review workspace module SHALL NOT own terminal rendering, background tasks, command palette filtering, raw-key input, or editor handoff.

#### Scenario: Task panel remains browser-owned
- **WHEN** the workspace switches review scope
- **THEN** current background task state SHALL remain attached to the browser session
- **AND** it SHALL NOT be persisted as workspace state
