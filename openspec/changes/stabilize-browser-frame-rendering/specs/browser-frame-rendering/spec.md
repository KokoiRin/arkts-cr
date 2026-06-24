## ADDED Requirements

### Requirement: Browser frame owns raw-key screen rendering
`cr browse` SHALL coordinate raw-key full redraws, task-panel partial refreshes, and prompt placement through a single browser frame state.

#### Scenario: Full redraw records the current frame
- **WHEN** raw-key browser mode performs a full screen redraw
- **THEN** the browser SHALL record the layout used for that redraw
- **AND** it SHALL record that a complete frame exists
- **AND** it SHALL record the task-panel contents rendered in that frame

#### Scenario: User command redraw replaces the previous frame
- **WHEN** a user command changes selection, mode, scope, filter, or scroll state
- **THEN** the next visible update SHALL be a full browser frame redraw
- **AND** any later partial task-panel refresh SHALL use the latest frame layout

### Requirement: Task-panel partial refresh is frame-safe
`cr browse` SHALL only perform task-panel partial refreshes when the last complete frame still matches the current screen layout.

#### Scenario: Task output changes with a valid frame
- **GIVEN** a complete browser frame has been rendered
- **AND** the current layout matches that frame
- **WHEN** build output changes while the user is idle
- **THEN** the browser SHALL update only the task-panel rows
- **AND** it SHALL preserve the command prompt cursor position
- **AND** it SHALL NOT clear the full screen

#### Scenario: Task output changes without a valid frame
- **GIVEN** no complete frame exists or the layout has changed since the last frame
- **WHEN** build output changes while the user is idle
- **THEN** the browser SHALL NOT write a partial task-panel update
- **AND** it SHALL request a full browser frame redraw

#### Scenario: Task output is unchanged
- **GIVEN** a complete browser frame has been rendered
- **WHEN** the task-panel text is unchanged
- **THEN** the browser SHALL NOT write a duplicate task-panel update

### Requirement: Temporary line input restores fixed frame
`cr browse` SHALL restore the fixed browser frame after temporary command or filter line input.

#### Scenario: Command prompt returns
- **WHEN** the user opens `:` command input and submits or cancels it
- **THEN** the browser SHALL mark the frame dirty
- **AND** the next raw-key visual update SHALL be a full browser frame redraw

#### Scenario: Filter prompt returns
- **WHEN** the user opens `/` filter input and submits or cancels it
- **THEN** the browser SHALL mark the frame dirty
- **AND** the next raw-key visual update SHALL be a full browser frame redraw
