## ADDED Requirements

### Requirement: Stop request grace period
`cr browse` SHALL track when a user requested a running background build to stop.

#### Scenario: User stops a running build
- **WHEN** a background build is running
- **AND** the user enters `stop` or `cancel`
- **THEN** the build state SHALL record the stop request time
- **AND** the build panel SHALL continue to show a stopping state until the process exits

### Requirement: Escalate unresponsive build stop
`cr browse` SHALL force-kill a stopped background build that remains running past the grace period.

#### Scenario: Build ignores graceful stop
- **WHEN** the user has requested a build stop
- **AND** the build process group is still running after the grace period
- **THEN** the browser SHALL send a force-kill signal to the build process group
- **AND** the build log SHALL show that stop was escalated

#### Scenario: No process group is available
- **WHEN** the user has requested a build stop
- **AND** no build process group id is available
- **AND** the build is still running after the grace period
- **THEN** the browser SHALL force-kill the parent build process
- **AND** the browser SHALL NOT crash

### Requirement: Stop escalation is idempotent
Stop escalation SHALL execute at most once for a single build.

#### Scenario: Poll continues after escalation
- **WHEN** stop escalation has already sent a force-kill signal
- **AND** the build process has not been reaped yet
- **THEN** subsequent polling SHALL NOT send another force-kill signal
- **AND** subsequent polling SHALL NOT append duplicate escalation log lines
