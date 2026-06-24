## ADDED Requirements

### Requirement: Browser shows file action diagnostics
The browser SHALL provide a `file actions` command that explains the resolved source for open, copy, and reveal actions.

#### Scenario: Show configured and fallback sources
- **WHEN** the user runs `file actions`
- **THEN** the browser SHALL show one diagnostic line for `open`
- **AND** SHALL show one diagnostic line for `copy`
- **AND** SHALL show one diagnostic line for `reveal`
- **AND** SHALL identify each action source as `cli`, `env`, `platform`, or `missing`
- **AND** SHALL NOT execute any file action

### Requirement: File action failures include source context
The browser SHALL include resolved command source context when a file action cannot run.

#### Scenario: Copy command fails
- **WHEN** `copy path` resolves to a configured command
- **AND** the command fails to launch or returns failure
- **THEN** the user-visible failure message SHALL include the source and command summary

#### Scenario: Reveal command is missing
- **WHEN** `reveal` has no configured command and no platform fallback
- **THEN** the user-visible failure message SHALL include that the source is `missing`

### Requirement: Editor handoff failures include source context
The browser SHALL include resolved command source context when editor handoff cannot run.

#### Scenario: Open command fails
- **WHEN** `open` resolves to a command
- **AND** the command fails to launch
- **THEN** the user-visible failure message SHALL include the source and command summary

#### Scenario: Open command is missing
- **WHEN** no open command can be resolved
- **THEN** the user-visible failure message SHALL include that the source is `missing`
