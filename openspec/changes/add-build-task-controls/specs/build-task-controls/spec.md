## ADDED Requirements

### Requirement: Stop running build
`cr browse` SHALL allow users to stop a running background build from the interactive browser.

#### Scenario: Stop a running build
- **WHEN** a build is running and the user enters a stop command
- **THEN** the browser SHALL request termination of the build process
- **AND** the build panel SHALL show a stopping or stopped state
- **AND** the browser SHALL remain in the current review view

#### Scenario: Stop when no build is running
- **WHEN** no build is running and the user enters a stop command
- **THEN** the browser SHALL keep the session open
- **AND** the build panel or command feedback SHALL explain that no build is running

### Requirement: Rerun build
`cr browse` SHALL allow users to rerun the configured build command after a prior build is not running.

#### Scenario: Rerun after build completes
- **WHEN** a build has completed or stopped and the user enters a rerun command
- **THEN** the browser SHALL start the configured build command again
- **AND** the build panel SHALL show the new build output

#### Scenario: Rerun while build is running
- **WHEN** a build is currently running and the user enters a rerun command
- **THEN** the browser SHALL NOT start a second build process
- **AND** the build panel SHALL tell the user to stop the current build first

### Requirement: Build lifecycle status
The build panel SHALL distinguish user-stopped builds from failed builds.

#### Scenario: User-stopped build exits
- **WHEN** the user has requested stop and the build process exits
- **THEN** the build panel SHALL show `stopped`
- **AND** the build log SHALL include `Build stopped.`

#### Scenario: Build exits without stop request
- **WHEN** the build process exits without a user stop request
- **THEN** the build panel SHALL continue to show `succeeded` for exit code 0
- **AND** the build panel SHALL continue to show `failed (<code>)` for non-zero exit codes
