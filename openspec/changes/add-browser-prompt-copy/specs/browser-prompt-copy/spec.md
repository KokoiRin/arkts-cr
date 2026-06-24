## ADDED Requirements

### Requirement: Browser copies prompt handoff
The browser SHALL provide commands that copy prompt-ready Markdown for the current review context to the configured clipboard action.

#### Scenario: Copy current visible scope prompt
- **WHEN** the user runs `copy prompt`
- **AND** visible changed files exist
- **THEN** the browser SHALL copy prompt-ready Markdown for the current visible changed files
- **AND** the copied text SHALL use the same Markdown handoff format as `cr review --prompt`
- **AND** the browser SHALL report how many files were copied into the prompt
- **AND** the browser SHALL keep the current page, selection, review scope, file filter, review progress, review notes, and task state unchanged

#### Scenario: Copy selected file prompt
- **WHEN** the user runs `copy prompt file`
- **AND** a selected visible changed file exists
- **THEN** the browser SHALL copy prompt-ready Markdown for only that file
- **AND** the copied text SHALL use the same Markdown handoff format as `cr review --prompt`
- **AND** the browser SHALL report that one file was copied into the prompt
- **AND** the browser SHALL keep the current page, selection, review scope, file filter, review progress, review notes, and task state unchanged

#### Scenario: Copy prompt with no visible files
- **WHEN** the user runs `copy prompt`
- **AND** no changed files are visible
- **THEN** the browser SHALL report that there are no changed files to copy
- **AND** SHALL NOT launch a clipboard command

#### Scenario: Copy selected file prompt with no selected file
- **WHEN** the user runs `copy prompt file`
- **AND** no selected visible changed file exists
- **THEN** the browser SHALL report that there is no changed file to copy
- **AND** SHALL NOT launch a clipboard command

#### Scenario: Copy command failure
- **WHEN** the user runs `copy prompt`
- **AND** the clipboard action fails
- **THEN** the browser SHALL show the existing source-aware copy failure message
