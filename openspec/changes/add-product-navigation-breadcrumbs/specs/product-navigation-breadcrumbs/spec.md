## ADDED Requirements

### Requirement: Browser context renders product navigation breadcrumbs
`cr browse` SHALL render the product navigation hierarchy in the context/status layer.

#### Scenario: Changed Files layer
- **GIVEN** the browser is showing the changed-file tree for a Review Scope
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: <scope> > Files`

#### Scenario: File Detail layer
- **GIVEN** the browser is showing a selected file detail
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: <scope> > Files > <path>`

#### Scenario: Commit picker layer
- **GIVEN** the browser is showing recent commits before a commit is selected
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: recent commits`
- **AND** it SHALL NOT append `> Files`

#### Scenario: Selected commit files
- **GIVEN** the user selected a commit as the Review Scope
- **WHEN** the browser shows that commit's changed-file tree
- **THEN** the context/status layer SHALL show `Scope: commit <short-sha> > Files`

#### Scenario: Status message
- **GIVEN** a raw-key action has produced a status message
- **WHEN** the context/status layer is rendered
- **THEN** the status message SHALL appear after the breadcrumb
