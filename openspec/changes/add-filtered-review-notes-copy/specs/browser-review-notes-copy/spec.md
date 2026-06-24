## MODIFIED Requirements

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
