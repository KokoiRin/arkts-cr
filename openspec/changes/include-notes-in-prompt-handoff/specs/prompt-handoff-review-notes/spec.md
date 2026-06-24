## MODIFIED Requirements

### Requirement: Browser copies prompt handoff
The browser SHALL provide commands that copy prompt-ready Markdown for the current review context to the configured clipboard action.

#### Scenario: Copy current visible scope prompt with review notes
- **WHEN** the user runs `copy prompt`
- **AND** visible changed files have review notes in the current Review Workspace
- **THEN** the copied prompt SHALL include matching review notes for those visible files
- **AND** SHALL NOT include review notes for files outside the copied visible file set
- **AND** the browser SHALL keep the current page, selection, Review Scope, file filter, progress markers, review notes, and task state unchanged

#### Scenario: Copy selected file prompt with review note
- **WHEN** the user runs `copy prompt file`
- **AND** the selected visible changed file has a review note
- **THEN** the copied prompt SHALL include that review note
- **AND** SHALL NOT include review notes for other files

### Requirement: Prompt renderer includes supplied review notes
The prompt renderer SHALL render supplied per-file review notes as part of the canonical Markdown handoff.

#### Scenario: Render file review note in summary and detail
- **WHEN** review data for a file contains `review_note`
- **THEN** `render_prompt_handoff` SHALL render `review note: ...` for that file under `## Files`
- **AND** SHALL render `review note: ...` for that file under `## Details`

#### Scenario: Preserve prompt format without notes
- **WHEN** review data contains no `review_note`
- **THEN** `render_prompt_handoff` SHALL preserve the existing no-note prompt structure
