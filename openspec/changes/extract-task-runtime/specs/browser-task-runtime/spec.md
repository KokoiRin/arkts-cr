## ADDED Requirements

### Requirement: Task runtime owns task lifecycle behavior
The system SHALL provide a browser task runtime module that owns command resolution, task state, background process lifecycle, output collection, stopping, stop escalation, rerun, foreground execution, and completion history.

#### Scenario: Command resolution remains unchanged
- **WHEN** the runtime resolves build, test, or lint commands
- **THEN** it SHALL preserve configured command handling, environment variable handling, missing-command behavior, and the DouyinHarmony build default

#### Scenario: Background task lifecycle remains unchanged
- **WHEN** the runtime starts and polls a configured task
- **THEN** it SHALL collect stdout lines, update return code, close stdout after completion, and append the same success, failure, stopped, or failed-to-start messages as before

#### Scenario: Stop and escalation behavior remains unchanged
- **WHEN** users stop a running task and the process does not exit inside the grace period
- **THEN** the runtime SHALL request process group termination first, then force kill the process group or parent process using the existing escalation behavior

#### Scenario: Rerun and history behavior remains unchanged
- **WHEN** users rerun the most recent completed task
- **THEN** the runtime SHALL rerun the same task kind, keep prior task history, and prevent starting a second process while one is running

### Requirement: Browser integrates through task runtime module
The browser SHALL call the task runtime module for task lifecycle operations while preserving Task Panel rendering and command behavior.

#### Scenario: Browser does not own task runtime helpers
- **WHEN** task lifecycle code is inspected
- **THEN** command resolution, start, stop, rerun, foreground execution, polling, output draining, and history recording SHALL live in `cr.ui.tasks`

#### Scenario: Task Panel rendering remains a browser concern
- **WHEN** the browser renders the bottom task panel
- **THEN** it SHALL continue to use TaskState and TaskRecord data without moving Browser Frame layout or terminal styling into the runtime module

#### Scenario: Existing task commands remain user-compatible
- **WHEN** users run `build`, `test`, `lint`, `stop`, or `rerun` in raw-key or line mode
- **THEN** the same foreground/background behavior, output panel behavior, and status history SHALL be preserved
