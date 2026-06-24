## ADDED Requirements

### Requirement: Browser stages selected file
The browser SHALL provide a selected-file command that stages the current changed file.

#### Scenario: Stage selected file
- **WHEN** the user runs `stage` with a changed file selected in a mutable local scope
- **THEN** the browser SHALL stage that repo-relative path through Git
- **AND** refresh the active Review Scope after the action succeeds
- **AND** show status feedback through the existing browser message/status area

#### Scenario: Stage with no selected file
- **WHEN** the user runs `stage` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without running Git

### Requirement: Browser unstages selected file
The browser SHALL provide a selected-file command that removes the current changed file from the index.

#### Scenario: Unstage selected file
- **WHEN** the user runs `unstage` with a changed file selected in a mutable local scope
- **THEN** the browser SHALL unstage that repo-relative path through Git
- **AND** refresh the active Review Scope after the action succeeds
- **AND** show status feedback through the existing browser message/status area

#### Scenario: Unstage with no selected file
- **WHEN** the user runs `unstage` and no changed file is available
- **THEN** the browser SHALL show missing-file feedback without running Git

### Requirement: Index actions preserve read-only review scopes
The browser SHALL NOT mutate Git index state while the active Review Scope is a read-only comparison scope.

#### Scenario: Stage in read-only scope
- **WHEN** the active scope is `base REF`, `range OLD..NEW`, or a selected commit scope
- **AND** the user runs `stage`
- **THEN** the browser SHALL report that index actions are only available for local worktree/index scopes
- **AND** SHALL NOT run Git staging

#### Scenario: Unstage in read-only scope
- **WHEN** the active scope is `base REF`, `range OLD..NEW`, or a selected commit scope
- **AND** the user runs `unstage`
- **THEN** the browser SHALL report that index actions are only available for local worktree/index scopes
- **AND** SHALL NOT run Git unstaging

### Requirement: Index actions use browser command infrastructure
The browser SHALL expose selected-file index actions through the existing parser, command palette, and action executor.

#### Scenario: Command palette lists index actions
- **WHEN** the command palette is rendered
- **THEN** `stage` and `unstage` SHALL appear as executable file commands
