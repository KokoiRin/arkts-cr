## ADDED Requirements

### Requirement: Browser Frame module owns screen-region layout
The system SHALL provide a Browser Frame rendering module that owns terminal height measurement, prompt row calculation, main-content height calculation, task-panel height calculation, and task-panel start-row calculation.

#### Scenario: Layout reserves prompt and task panel regions
- **WHEN** a background task is present on a 12-row terminal
- **THEN** the Browser Frame module SHALL reserve the final row for the prompt and place the task panel above it without consuming the main content region entirely

#### Scenario: Layout without task keeps prompt at bottom
- **WHEN** no background task is present on a 12-row terminal
- **THEN** the Browser Frame module SHALL reserve the final row for the prompt and give the remaining rows to main content

### Requirement: Browser Frame module owns Task Panel presentation
The system SHALL render Task Panel lines from `TaskState`, `TaskRecord` history, and terminal style without depending on browser navigation state or review workspace state.

#### Scenario: Running task panel includes status command and output
- **WHEN** a task has a command, status, and captured output lines
- **THEN** the Browser Frame module SHALL render the panel divider, task label/status/command line, and the latest output lines within the requested height

#### Scenario: Task history is shown compactly
- **WHEN** task history is provided
- **THEN** the Browser Frame module SHALL render a compact recent-history line before the task output body

### Requirement: Browser Frame module owns partial Task Panel refresh
The system SHALL perform Task Panel-only refreshes without clearing the full browser screen and SHALL refuse partial refreshes when the cached frame is dirty, incomplete, or laid out for a different terminal size.

#### Scenario: Partial refresh updates only task panel rows
- **WHEN** the current task panel lines differ from the last rendered panel and the cached frame is complete and current
- **THEN** the Browser Frame module SHALL emit cursor-save, task-panel row positioning, per-row clearing, fitted task-panel lines, and cursor-restore sequences without emitting a full-screen clear

#### Scenario: Dirty frame refuses partial refresh
- **WHEN** the cached frame is marked dirty
- **THEN** the Browser Frame module SHALL emit no terminal output, keep the frame dirty, and report that no partial refresh occurred

#### Scenario: Unchanged panel emits nothing
- **WHEN** the newly rendered task panel lines match the cached panel
- **THEN** the Browser Frame module SHALL emit no terminal output and report that no partial refresh occurred

### Requirement: Browser keeps page rendering orchestration
The browser SHALL continue to own page-specific main content generation, command execution, prompt input flow, and workspace save/restore orchestration while delegating Browser Frame and Task Panel presentation implementation to the frame module.

#### Scenario: Browser wrappers preserve existing behavior
- **WHEN** existing browser helper entry points such as `_screen_layout`, `_task_panel_lines`, `_draw_task_panel_only`, and `_fit_terminal_line` are called
- **THEN** they SHALL return the same observable results through delegation to the Browser Frame module
