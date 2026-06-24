## ADDED Requirements

### Requirement: Background build process group
`cr browse` SHALL run each interactive background build in an isolated process group when the platform supports it.

#### Scenario: Start background build
- **WHEN** the browser starts a background build
- **THEN** the build process SHALL be started in an isolated process group
- **AND** the build state SHALL remember the process group id

### Requirement: Stop build process group
`cr browse` SHALL stop the whole background build process group when the user cancels a running build.

#### Scenario: Stop build with child processes
- **WHEN** a background build has spawned child processes
- **AND** the user enters `stop` or `cancel`
- **THEN** the browser SHALL request termination of the build process group
- **AND** child processes in that group SHALL not continue running after the build is stopped
- **AND** the browser SHALL remain in the current review view

#### Scenario: Process group termination fails
- **WHEN** the user stops a running build
- **AND** terminating the build process group fails
- **THEN** the browser SHALL try to terminate the parent build process
- **AND** the build panel SHALL show a readable stop failure message

### Requirement: Existing build states remain stable
Process group cleanup SHALL preserve the existing build panel lifecycle states.

#### Scenario: User-stopped build exits
- **WHEN** the user has requested stop and the build process exits
- **THEN** the build panel SHALL continue to show `stopped`
- **AND** the build log SHALL continue to include `Build stopped.`
