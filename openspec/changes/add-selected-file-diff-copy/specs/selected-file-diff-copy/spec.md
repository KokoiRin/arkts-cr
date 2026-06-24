## ADDED Requirements

### Requirement: Copy selected file diff snippet
The browser SHALL let users copy a compact review diff snippet for the currently
selected changed file.

#### Scenario: Copy selected file diff
- **WHEN** the user runs `copy diff` with a visible changed file selected
- **THEN** the browser SHALL copy a Markdown snippet for exactly that file
- **AND** the snippet SHALL include the selected file path and diff hunks
- **AND** the browser SHALL preserve page, selection, review scope, filters,
  progress, notes, and task state

#### Scenario: Empty selected file diff copy
- **WHEN** the user runs `copy diff` without a visible changed file
- **THEN** the browser SHALL report that no changed file can be copied
- **AND** it SHALL NOT invoke the copy command

#### Scenario: Copy failure
- **WHEN** the configured copy command fails
- **THEN** the browser SHALL surface the copy failure message

### Requirement: Selected file diff snippet is not prompt handoff
The selected file diff snippet SHALL be rendered as compact review context, not
as the full AI review handoff prompt.

#### Scenario: Render compact file snippet
- **WHEN** selected file diff copy renders snippet text
- **THEN** it SHALL include selected-file review facts such as summary, anchor,
seen state, review note, purpose/focus, risks, and hunks when present
- **AND** it SHALL NOT include full prompt request language
