## ADDED Requirements

### Requirement: Background task runtime uses task naming
The browser's background task runtime SHALL use task-oriented names for the current task state and task lifecycle helpers.

#### Scenario: Current task state
- **WHEN** maintainers inspect `src/cr/ui/browser.py`
- **THEN** the current background task field SHALL be named as a task
- **AND** the state class SHALL be named `TaskState`
- **AND** the main lifecycle path SHALL NOT rely on `BuildState` as the runtime model

#### Scenario: Task lifecycle helpers
- **WHEN** maintainers inspect task lifecycle helpers
- **THEN** polling, recording, panel rendering, stopping, rerunning, output draining, and stop escalation SHALL use task-oriented helper names

### Requirement: User-visible task behavior remains stable
Task state naming changes SHALL preserve existing build/test/lint behavior.

#### Scenario: Existing task commands
- **WHEN** the user runs `build`, `test`, `lint`, `stop`, or `rerun`
- **THEN** the browser SHALL keep the same task behavior as before the rename

#### Scenario: Build command discovery
- **WHEN** build command discovery runs
- **THEN** build-specific default detection such as DouyinHarmony SHALL remain build-specific
- **AND** test/lint command discovery SHALL remain explicitly configured
