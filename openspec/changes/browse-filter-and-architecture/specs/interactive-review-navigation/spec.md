## ADDED Requirements

### Requirement: Browse file list filtering
`cr browse` SHALL allow users to filter the interactive changed-file list by Git path during a review session.

#### Scenario: Apply a filter from the interactive list
- **WHEN** the user enters a non-empty filter query
- **THEN** the browser shows only changed files whose full Git path contains the query case-insensitively
- **AND** navigation, numeric selection, file opening, and next/previous commands operate on the filtered file list

#### Scenario: Show active filter status
- **WHEN** a filter is active
- **THEN** the browser displays the active filter query
- **AND** the browser displays the filtered match count relative to the total changed-file count
- **AND** the browser displays a clear-filter command

#### Scenario: Clear a filter
- **WHEN** a filter is active and the user clears it
- **THEN** the browser shows the full changed-file list again
- **AND** the selected index remains within the visible list

#### Scenario: Refresh with a filter
- **WHEN** a filter is active and the user refreshes the browser
- **THEN** the browser reloads changed files from Git
- **AND** reapplies the existing filter query
- **AND** clamps the selected index to the refreshed filtered list

### Requirement: Browse non-TTY compatibility
`cr browse` SHALL preserve line-oriented operation when stdin or stdout is not an interactive TTY.

#### Scenario: Filter from line mode
- **WHEN** `cr browse` runs in non-TTY mode and receives `/query` or `filter query`
- **THEN** the browser applies the query as a path filter
- **AND** subsequent line-mode selections operate on the filtered file list

#### Scenario: Existing line-mode commands keep working
- **WHEN** `cr browse` runs in non-TTY mode
- **THEN** existing commands for list, numeric selection, next, previous, refresh, open, help, and quit continue to work

### Requirement: Browser module locality
Interactive browse behavior SHALL be owned by a dedicated browser module instead of the CLI argument parsing module.

#### Scenario: CLI dispatches to browser module
- **WHEN** the `browse` command is invoked
- **THEN** the CLI delegates browser execution to the browser module through a small function interface
- **AND** browse state transitions and rendering are implemented outside the CLI parser module
