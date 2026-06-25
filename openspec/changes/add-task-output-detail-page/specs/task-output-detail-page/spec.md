## ADDED Requirements

### Requirement: Browser opens current task output page

`cr browse` SHALL provide a page that displays the current task output inside the browser.

#### Scenario: Open Task Output page

- **WHEN** the user runs `task output` or `output`
- **THEN** the browser SHALL enter Task Output page
- **AND** the page SHALL participate in browser back/forward page history
- **AND** the page SHALL reset its task-output scroll position when opened

#### Scenario: Render current task output

- **GIVEN** a current build, test, or lint task exists
- **WHEN** Task Output page renders
- **THEN** the page SHALL show the task label, task status, command, and captured output lines
- **AND** the page SHALL expose contextual actions for copying, saving, stopping, rerunning, and returning

#### Scenario: Render empty current task output

- **GIVEN** no current task exists
- **WHEN** Task Output page renders
- **THEN** the page SHALL show an empty current-task output state
- **AND** it SHALL NOT synthesize output from task history

### Requirement: Task Output page scrolls independently

Task Output page SHALL maintain its own scroll state separate from Changed Files and File Detail.

#### Scenario: Scroll task output

- **GIVEN** Task Output page is visible with more captured output than fits on screen
- **WHEN** the user presses `up`, `down`, `pageup`, `pagedown`, `home`, or `end`
- **THEN** the browser SHALL update task-output scroll within valid bounds
- **AND** it SHALL NOT change selected file or File Detail scroll

### Requirement: Running task refresh preserves ordinary page stability

Running task output SHALL continue to avoid full-screen redraws on ordinary pages while keeping Task Output page live.

#### Scenario: Ordinary page uses Task Panel refresh

- **GIVEN** a task is running
- **AND** the user is on Changed Files, File Detail, Scope Home, Commit Picker, or Command Palette
- **WHEN** the browser receives an idle task tick
- **THEN** the browser SHALL try the existing Task Panel-only refresh path

#### Scenario: Task Output page redraws main content

- **GIVEN** a task is running
- **AND** the user is on Task Output page
- **WHEN** the browser receives an idle task tick
- **THEN** the browser SHALL schedule a full browser redraw
- **AND** it SHALL NOT use the Task Panel-only refresh path for that tick
