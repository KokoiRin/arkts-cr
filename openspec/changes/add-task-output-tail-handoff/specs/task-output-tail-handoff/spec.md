## ADDED Requirements

### Requirement: Copy current task output tail

The browser SHALL support copying a compact tail of the current task output.

#### Scenario: Copy default task output tail
- **GIVEN** a current build/test/lint task with captured output lines
- **WHEN** the user runs `copy task tail`
- **THEN** the copied Markdown SHALL include task type, status, command, and only the last 40 captured output lines

#### Scenario: Copy custom-size task output tail
- **GIVEN** a current task with captured output lines
- **WHEN** the user runs `copy task tail 5`
- **THEN** the copied Markdown SHALL include only the last 5 captured output lines

#### Scenario: Copy task output tail without task
- **GIVEN** no current task exists
- **WHEN** the user runs `copy task tail`
- **THEN** the browser SHALL report that no task output tail can be copied
- **AND** it MUST NOT call the clipboard command

### Requirement: Save current task output tail

The browser SHALL support saving a compact tail of the current task output.

#### Scenario: Save default task output tail
- **GIVEN** a current task with captured output lines
- **WHEN** the user runs `save task tail`
- **THEN** the browser SHALL write tail Markdown to `.cr/handoff/task-output-tail.md`

#### Scenario: Save task output tail to custom path
- **GIVEN** a current task with captured output lines
- **WHEN** the user runs `save task tail tmp/tail.md`
- **THEN** the browser SHALL write tail Markdown to the requested path

#### Scenario: Save task output tail without task
- **GIVEN** no current task exists
- **WHEN** the user runs `save task tail`
- **THEN** the browser SHALL report that no task output tail can be saved
- **AND** it MUST NOT write a file

### Requirement: Keep task tail handoff lightweight

Task output tail handoff MUST NOT change task lifecycle, task history, Problems parsing, task output capture capacity, or workspace persistence.

#### Scenario: Tail handoff is a snapshot
- **GIVEN** a task is still running
- **WHEN** the user copies or saves task output tail
- **THEN** the handoff SHALL use the currently captured output snapshot
- **AND** the task SHALL continue running normally
