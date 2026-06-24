## ADDED Requirements

### Requirement: Command palette filters executable commands
`cr browse` SHALL allow users to filter executable command palette entries.

#### Scenario: Filter palette commands
- **GIVEN** commands mode is active
- **WHEN** the user enters a command palette filter
- **THEN** the palette SHALL show only executable commands whose group, label, command, or description contains the filter text case-insensitively
- **AND** the selected palette row SHALL clamp to the filtered results

#### Scenario: Empty palette filter result
- **GIVEN** commands mode is active
- **WHEN** the command palette filter matches no executable commands
- **THEN** the palette SHALL show an empty-result message
- **AND** pressing Enter SHALL NOT execute a stale command

### Requirement: Command palette filter is independent from file filter
Command palette search SHALL NOT modify file path filtering.

#### Scenario: Search command palette
- **GIVEN** commands mode is active
- **WHEN** the user presses `/` and enters a command filter
- **THEN** the browser SHALL update the command palette filter
- **AND** it SHALL NOT update the changed-file path filter

#### Scenario: Clear command palette filter
- **GIVEN** commands mode is active
- **AND** the changed-file path filter is set
- **AND** the command palette filter is set
- **WHEN** the user enters `c` or `clear`
- **THEN** the browser SHALL clear the command palette filter
- **AND** it SHALL keep the changed-file path filter unchanged

### Requirement: Filtered palette commands execute normally
Filtered command palette results SHALL execute through the existing command handling path.

#### Scenario: Execute filtered command
- **GIVEN** commands mode is active
- **AND** the command palette filter leaves a matching executable command selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute that filtered command
- **AND** it SHALL use the same command handling path as a typed command
