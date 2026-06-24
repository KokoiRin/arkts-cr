## ADDED Requirements

### Requirement: Browser uses explicit page layers
`cr browse` raw-key mode SHALL render the screen as a single frame composed of context/status, main content, background task panel, and input prompt layers.

#### Scenario: Full redraw with a running task
- **GIVEN** a background build exists
- **WHEN** the browser performs a full redraw
- **THEN** it SHALL render context/status above the main content
- **AND** it SHALL render the task panel above the final prompt row
- **AND** it SHALL place the prompt on the final terminal row

### Requirement: Raw-key feedback stays inside the browser frame
Raw-key browser actions SHALL NOT print ordinary feedback outside the fixed frame.

#### Scenario: Open selected file in raw-key mode
- **WHEN** the user opens a selected file
- **THEN** the browser SHALL show the result in the context/status layer
- **AND** it SHALL schedule a full redraw
- **AND** it SHALL NOT append feedback below the prompt

#### Scenario: Invalid selection in raw-key mode
- **WHEN** the user enters an invalid numeric selection
- **THEN** the browser SHALL show the validation message in the context/status layer
- **AND** it SHALL schedule a full redraw

#### Scenario: Unknown command in raw-key mode
- **WHEN** the user enters an unknown command
- **THEN** the browser SHALL show a compact unknown-command message in the context/status layer
- **AND** it SHALL schedule a full redraw

### Requirement: Task panel partial refresh respects frame ownership
Background task partial refresh SHALL only write to the task panel when the existing browser frame is complete and still owns the terminal layout.

#### Scenario: Frame is incomplete or dirty
- **GIVEN** the browser frame is incomplete or dirty
- **WHEN** build output changes
- **THEN** the task panel partial refresh SHALL refuse to write
- **AND** the browser SHALL perform a later full redraw

#### Scenario: Status message is pending
- **GIVEN** a raw-key action has produced a status message that has not been rendered by a full redraw
- **WHEN** build output changes
- **THEN** the task panel partial refresh SHALL refuse to write over the stale frame
