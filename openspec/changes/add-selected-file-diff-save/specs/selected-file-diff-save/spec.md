## ADDED Requirements

### Requirement: Save selected file diff snippet
The browser SHALL let users save a compact review diff snippet for the currently
selected changed file.

#### Scenario: Save selected file diff to default path
- **WHEN** the user runs `save diff` with a visible changed file selected
- **THEN** the browser SHALL save a Markdown snippet for exactly that file to
  `.cr/handoff/review-diff.md`
- **AND** the browser SHALL preserve page, selection, review scope, filters,
  progress, notes, and task state

#### Scenario: Save selected file diff to requested path
- **WHEN** the user runs `save diff PATH` with a visible changed file selected
- **THEN** the browser SHALL save the selected file Markdown snippet to `PATH`
- **AND** relative paths SHALL resolve from the repository root

#### Scenario: Empty selected file diff save
- **WHEN** the user runs `save diff` without a visible changed file
- **THEN** the browser SHALL report that no changed file can be saved
- **AND** it SHALL NOT write a file

#### Scenario: Save failure
- **WHEN** the selected file diff snippet cannot be written
- **THEN** the browser SHALL surface the write failure message
