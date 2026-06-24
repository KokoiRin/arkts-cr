## ADDED Requirements

### Requirement: Browser displays active review scope
`cr browse` SHALL display the active review scope in the interactive browser context area.

#### Scenario: Default worktree scope
- **WHEN** the browser is reviewing default unstaged worktree changes
- **THEN** the browser SHALL display `Scope: worktree`

#### Scenario: Non-default local scopes
- **WHEN** the browser is reviewing staged changes
- **THEN** the browser SHALL display `Scope: staged`
- **WHEN** the browser is reviewing combined local changes
- **THEN** the browser SHALL display `Scope: all local changes`

#### Scenario: Ref comparison scopes
- **WHEN** the browser is reviewing changes from a base ref
- **THEN** the browser SHALL display `Scope: base <ref>`
- **WHEN** the browser is reviewing an explicit ref range
- **THEN** the browser SHALL display `Scope: range <old>..<new>`

#### Scenario: Commit scopes
- **WHEN** the browser is showing recent commits
- **THEN** the browser SHALL display `Scope: recent commits`
- **WHEN** the browser is reviewing a selected commit
- **THEN** the browser SHALL display `Scope: commit <short-hash>`

### Requirement: Browser switches review scope in-session
`cr browse` SHALL allow users to switch review scopes from the command prompt without restarting the browser.

#### Scenario: Switch between local scopes
- **WHEN** the user enters `staged`
- **THEN** the browser SHALL reload changed files for staged changes
- **AND** display `Scope: staged`
- **WHEN** the user enters `all`
- **THEN** the browser SHALL reload changed files for combined local changes
- **AND** display `Scope: all local changes`
- **WHEN** the user enters `worktree`
- **THEN** the browser SHALL reload changed files for default worktree changes
- **AND** display `Scope: worktree`

#### Scenario: Switch to ref comparison scopes
- **WHEN** the user enters `base <ref>`
- **THEN** the browser SHALL reload changed files for that base ref comparison
- **AND** display `Scope: base <ref>`
- **WHEN** the user enters `range <old>..<new>`
- **THEN** the browser SHALL reload changed files for that explicit ref range
- **AND** display `Scope: range <old>..<new>`

#### Scenario: Scope switch resets view-local state
- **WHEN** the user switches review scope
- **THEN** the browser SHALL clear the active file filter
- **AND** reset selection, file scroll, list scroll, and render caches
