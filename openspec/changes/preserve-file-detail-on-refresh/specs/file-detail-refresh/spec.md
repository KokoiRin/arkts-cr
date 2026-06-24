## ADDED Requirements

### Requirement: Preserve File Detail on ordinary refresh
The browser SHALL keep users in File Detail after ordinary refresh when the
selected file is still visible in the refreshed Review Scope.

#### Scenario: Selected file survives refresh
- **WHEN** the user runs `refresh` from File Detail
- **AND** the selected path is still present after reloading changed files and
  applying the active filters
- **THEN** the browser SHALL remain in File Detail
- **AND** it SHALL keep that path selected
- **AND** it SHALL clamp the previous file scroll to the refreshed File Detail
  height
- **AND** it SHALL reset page back/forward history for the reloaded scope

#### Scenario: Selected file disappears on refresh
- **WHEN** the user runs `refresh` from File Detail
- **AND** the selected path is no longer visible after reloading changed files
- **THEN** the browser SHALL show Changed Files
- **AND** it SHALL reset File Detail scroll
- **AND** it SHALL report that the current file is no longer changed

#### Scenario: Index-action refresh is unchanged
- **WHEN** a successful `stage` or `unstage` action refreshes the Review Scope
- **THEN** the browser SHALL continue to show Changed Files after the action
