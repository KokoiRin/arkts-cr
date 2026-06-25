# Task Output First Problem Handoff

## ADDED Requirements

### Requirement: Task Output can open the first parsed problem

The Task Output page SHALL allow `view problem` to open the Source File page for
the first visible parsed task problem.

#### Scenario: View first parsed problem from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains repo-local parseable problems
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL open Source File at the first visible problem path and line
- **AND** Back SHALL return to Task Output

#### Scenario: No parsed problem exists

- **GIVEN** the browser is on Task Output
- **AND** the current task output has no visible parseable problems
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL stay on Task Output
- **AND** the status SHALL say no task problem can be viewed

### Requirement: Task Output can hand off first parsed problem context

The Task Output page SHALL allow `copy problem context` and
`save problem context [PATH]` to use the first visible parsed task problem.

#### Scenario: Copy first problem context from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains a repo-local parseable problem
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL contain the selected problem facts
- **AND** it SHALL include source context for that problem line

#### Scenario: Save first problem context from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains a repo-local parseable problem
- **WHEN** the user runs `save problem context PATH`
- **THEN** the same first-problem context SHALL be written to PATH
