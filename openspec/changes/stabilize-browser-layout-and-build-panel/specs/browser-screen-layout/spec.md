## ADDED Requirements

### Requirement: Browser screen regions
`cr browse` SHALL render interactive TTY sessions using stable screen regions for content, background task output, and command input.

#### Scenario: Render with no background task
- **WHEN** the browser has no active build panel
- **THEN** the main content region SHALL use the available terminal rows above the input prompt
- **AND** the input prompt SHALL remain on the final terminal row

#### Scenario: Render with a build panel
- **WHEN** a build panel is present
- **THEN** the main content region SHALL shrink to leave room for the build panel
- **AND** the build panel SHALL render above the input prompt
- **AND** the input prompt SHALL remain below the build panel

### Requirement: Build panel isolated refresh
`cr browse` SHALL update build output without scrolling or clearing the main browser screen.

#### Scenario: Background build output changes
- **WHEN** the build process emits new output while the user is idle
- **THEN** the browser SHALL update only the build panel rows
- **AND** the browser SHALL NOT clear the full screen
- **AND** the browser SHALL preserve the cursor position used for command input

#### Scenario: Background build output unchanged
- **WHEN** the build panel contents have not changed since the previous render
- **THEN** the browser SHALL NOT write a duplicate panel frame

### Requirement: Raw-key commands do not scroll the screen
`cr browse` SHALL treat raw-key input as command events instead of terminal text output.

#### Scenario: User presses a navigation key
- **WHEN** raw-key mode reads a navigation key, selection key, or page key
- **THEN** command reading SHALL NOT print an extra newline
- **AND** the next visible change SHALL come from fixed-area redraw or isolated panel refresh

#### Scenario: User enters line input intentionally
- **WHEN** the user opens filter input or command input
- **THEN** the browser MAY show a dedicated line prompt for that input
- **AND** returning from that input SHALL restore fixed-region rendering on the next redraw
