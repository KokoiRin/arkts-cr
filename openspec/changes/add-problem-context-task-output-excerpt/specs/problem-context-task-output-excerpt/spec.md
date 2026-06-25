## ADDED Requirements

### Requirement: Problem context includes task output excerpt for task problems

The browser SHALL include a compact Task Output excerpt centered on the
problem's original output line when focused Problem Context Markdown is
generated from a parsed task problem.

#### Scenario: Copy selected task problem context with output excerpt

- **GIVEN** Task Problems has a selected problem parsed from captured task output
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the selected problem, nearby source,
  same-file diff context when available, and a Task Output excerpt containing the
  selected problem output line.

#### Scenario: Save first task-output problem context with output excerpt

- **GIVEN** Task Output has at least one visible parsed problem
- **WHEN** the user runs `save problem context`
- **THEN** the saved Markdown SHALL include a Task Output excerpt centered on the
  first visible parsed problem's output line.

### Requirement: Source page context remains source focused

The browser SHALL NOT add a Task Output excerpt to Problem Context Markdown
generated directly from Source File Page unless an active task problem target is
used.

#### Scenario: Copy source page problem context

- **GIVEN** Source File Page is open for a source file and line
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include source and diff context
- **AND** it SHALL NOT include a Task Output section.
