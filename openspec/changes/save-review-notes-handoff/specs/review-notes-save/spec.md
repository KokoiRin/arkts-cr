## ADDED Requirements

### Requirement: Save Review Notes Summary

The browser SHALL save the current Review Notes summary as Markdown-like plain text.

#### Scenario: Save notes to default path

- **GIVEN** the workspace has review notes
- **WHEN** the user runs `save notes`
- **THEN** cr writes `.cr/handoff/review-notes.md`
- **AND** the file uses the same ordered summary as `notes` and `copy notes`
- **AND** the browser keeps the current page, selection, task state, filters, and review progress

#### Scenario: Save notes to requested path

- **GIVEN** the workspace has review notes
- **WHEN** the user runs `save notes tmp/notes.md`
- **THEN** cr writes `tmp/notes.md`

#### Scenario: No notes to save

- **GIVEN** the workspace has no review notes
- **WHEN** the user runs `save notes`
- **THEN** cr does not write a file
- **AND** reports `No review notes to save.`
