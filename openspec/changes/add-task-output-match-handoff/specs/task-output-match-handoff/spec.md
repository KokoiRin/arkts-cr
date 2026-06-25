# task-output-match-handoff Specification

## ADDED Requirements

### Requirement: Copy current Task Output match

The browser SHALL support `copy task match` when a current task has output and Task Output find text exists.

#### Scenario: Copy excerpt around current match

- **GIVEN** Task Output has captured lines
- **AND** the user has run `find TEXT`
- **AND** the current task output focus is on a matching line
- **WHEN** the user runs `copy task match`
- **THEN** the copied Markdown includes the query
- **AND** includes up to three lines before and after the focused line
- **AND** marks the focused line with `>`
- **AND** includes line numbers.

#### Scenario: Missing find text

- **GIVEN** Task Output has captured lines
- **AND** no Task Output find text exists
- **WHEN** the user runs `copy task match`
- **THEN** no clipboard write is attempted
- **AND** the browser reports `Run find TEXT first.`

### Requirement: Save current Task Output match

The browser SHALL support `save task match [PATH]` using the same excerpt as `copy task match`.

#### Scenario: Save default path

- **GIVEN** Task Output has captured lines
- **AND** the user has run `find TEXT`
- **WHEN** the user runs `save task match`
- **THEN** the excerpt is written to `.cr/handoff/task-output-match.md`.
