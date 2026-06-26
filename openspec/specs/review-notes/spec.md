# Review Notes Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Per-file review notes, note summaries, note filtering, copying, saving, and persistence.

## Requirements
### Requirement: Browser clears selected file notes
The browser SHALL let users clear the currently selected file note without editing persisted JSON by hand.

#### Scenario: Clear selected file note
- **WHEN** the selected file already has a note
- **AND** the user runs `note`
- **THEN** the selected file note SHALL be removed
- **AND** the browser SHALL report that the note was cleared

### Requirement: Browser records per-file review notes
The browser SHALL let users set or replace one note for the currently selected changed file.

#### Scenario: Set selected file note
- **WHEN** the user runs `note check lifecycle edge case`
- **AND** a changed file is selected
- **THEN** the selected file SHALL store the note text `check lifecycle edge case`
- **AND** the browser SHALL remain in the current review context
- **AND** SHALL NOT start or stop any task process

### Requirement: Browser renders review notes in review layers
The browser SHALL surface review notes where users scan and read changed files.

#### Scenario: Show note in changed files and file detail
- **WHEN** a changed file has a note
- **THEN** the Changed Files row SHALL show a compact note marker
- **AND** the File Detail header area SHALL show the full note text

### Requirement: Browser persists review notes with workspace state
The browser SHALL save and restore per-file review notes in the default workspace state.

#### Scenario: Restore saved note
- **WHEN** `.git/cr/browse-state.json` contains `review_notes` for a changed file
- **AND** the next default browser session restores workspace state
- **THEN** the restored browser state SHALL include that file note
- **AND** task history SHALL remain excluded from workspace persistence

### Requirement: Browser summarizes review notes
The browser SHALL provide a command that lists all current review notes without changing the active review layer.

#### Scenario: Show ordered review notes
- **WHEN** the user runs `notes`
- **AND** review notes exist for changed files in the active review scope
- **THEN** the browser SHALL show a `Review notes:` summary
- **AND** notes for current changed files SHALL be ordered by the current review list order
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Show persisted notes outside current changes
- **WHEN** the user runs `notes`
- **AND** `review_notes` contains paths that are not in the active changed files
- **THEN** the browser SHALL include those notes after current changed-file notes
- **AND** those extra notes SHALL be ordered by path

#### Scenario: Show empty review notes state
- **WHEN** the user runs `notes`
- **AND** no review notes exist
- **THEN** the browser SHALL show a clear empty state

### Requirement: Browser copies review notes summary
The browser SHALL provide a command that copies the current review notes summary to the configured clipboard action.

#### Scenario: Copy ordered review notes
- **WHEN** the user runs `copy notes`
- **AND** review notes exist
- **THEN** the browser SHALL copy the same ordered text that `notes` shows
- **AND** the browser SHALL report how many review notes were copied
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Copy filtered review notes
- **WHEN** the user runs `copy notes lifecycle`
- **AND** review notes match `lifecycle`
- **THEN** the browser SHALL copy the same ordered text that `notes lifecycle` shows
- **AND** the browser SHALL report how many matching review notes were copied
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Copy filtered review notes with no matches
- **WHEN** the user runs `copy notes owner`
- **AND** review notes exist but none match `owner`
- **THEN** the browser SHALL report that there are no matching review notes to copy
- **AND** SHALL NOT launch a clipboard command

#### Scenario: Copy review notes from notes alias
- **WHEN** the user runs `notes copy`
- **THEN** the browser SHALL keep copying the full notes summary

### Requirement: Browser filters review notes by query
The browser SHALL provide a command that filters the review notes summary by path or note text.

#### Scenario: Match note text
- **WHEN** the user runs `notes lifecycle`
- **AND** a review note contains `lifecycle`
- **THEN** the browser SHALL show only matching notes
- **AND** SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Match path text case-insensitively
- **WHEN** the user runs `notes sample`
- **AND** a review note path contains `Sample` with different casing
- **THEN** the browser SHALL include that note

#### Scenario: No filtered matches
- **WHEN** the user runs `notes owner`
- **AND** review notes exist but none match `owner`
- **THEN** the browser SHALL show a clear no-match state

#### Scenario: Empty query keeps existing summary
- **WHEN** the user runs `notes`
- **THEN** the browser SHALL keep showing all review notes

### Requirement: Review Notes behavior remains stable
Extracting the module SHALL NOT change user-visible Review Notes behavior.

#### Scenario: Preserve ordering and filtering
- **WHEN** notes are shown or copied
- **THEN** current changed-file notes SHALL remain ordered by changed-file order
- **AND** persisted extra notes SHALL follow sorted by path
- **AND** filtering SHALL remain case-insensitive over path and note text

#### Scenario: Preserve empty states
- **WHEN** there are no notes or no matching filtered notes
- **THEN** the browser SHALL report the same empty-state messages as before

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

### Requirement: Review Notes rules are module-owned
The browser SHALL keep Review Notes summary, filtering, ordering, and copy
message rules in a dedicated UI module.

#### Scenario: Render review notes through module
- **WHEN** the browser needs `notes` or `notes QUERY` output
- **THEN** it SHALL delegate note ordering, filtering, and empty-state text to
  the Review Notes module

#### Scenario: Copy review notes through module
- **WHEN** the browser needs `copy notes` or `copy notes QUERY`
- **THEN** it SHALL delegate rendered text and copy status messages to the
  Review Notes module

### Requirement: Prompt renderer includes supplied review notes
The prompt renderer SHALL render supplied per-file review notes as part of the canonical Markdown handoff.

#### Scenario: Render file review note in summary and detail
- **WHEN** review data for a file contains `review_note`
- **THEN** `render_prompt_handoff` SHALL render `review note: ...` for that file under `## Files`
- **AND** SHALL render `review note: ...` for that file under `## Details`

#### Scenario: Preserve prompt format without notes
- **WHEN** review data contains no `review_note`
- **THEN** `render_prompt_handoff` SHALL preserve the existing no-note prompt structure
