## ADDED Requirements

### Requirement: Browser copies review notes summary
The browser SHALL provide a command that copies the current review notes summary to the configured clipboard action.

#### Scenario: Copy ordered review notes
- **WHEN** the user runs `copy notes`
- **AND** review notes exist
- **THEN** the browser SHALL copy the same ordered text that `notes` shows
- **AND** the browser SHALL report how many review notes were copied
- **AND** the browser SHALL keep the current page, selection, review scope, and task state unchanged

#### Scenario: Copy review notes from notes alias
- **WHEN** the user runs `notes copy`
- **THEN** the browser SHALL perform the same action as `copy notes`

#### Scenario: Copy with no review notes
- **WHEN** the user runs `copy notes`
- **AND** no review notes exist
- **THEN** the browser SHALL report that there are no review notes to copy
- **AND** SHALL NOT launch a clipboard command

#### Scenario: Copy command failure
- **WHEN** the user runs `copy notes`
- **AND** the clipboard action fails
- **THEN** the browser SHALL show the existing source-aware copy failure message
