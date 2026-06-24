## ADDED Requirements

### Requirement: Save current visible prompt handoff
The browser SHALL support `save prompt [PATH]` to write prompt-ready Markdown for the current visible changed files to a file.

#### Scenario: Save visible scope to default path
- **WHEN** the current browser scope has visible changed files and the user runs `save prompt`
- **THEN** the browser SHALL write the same prompt-ready Markdown used by `copy prompt` to `.cr/handoff/review-prompt.md`
- **AND** the browser SHALL report the saved repo-relative path without changing page, selection, Review Scope, file filter, progress markers, review notes, or task state

#### Scenario: Save visible scope to explicit path
- **WHEN** the current browser scope has visible changed files and the user runs `save prompt tmp/review.md`
- **THEN** the browser SHALL write the prompt-ready Markdown to `tmp/review.md` relative to the repository root

### Requirement: Save selected file prompt handoff
The browser SHALL support `save prompt file [PATH]` to write prompt-ready Markdown for only the selected visible changed file to a file.

#### Scenario: Save selected file to default path
- **WHEN** the current browser scope has a selected visible changed file and the user runs `save prompt file`
- **THEN** the browser SHALL write the same prompt-ready Markdown used by `copy prompt file` to `.cr/handoff/review-prompt-file.md`
- **AND** the generated handoff SHALL include review notes only for the selected file

#### Scenario: Save selected file to explicit path
- **WHEN** the current browser scope has a selected visible changed file and the user runs `save prompt file tmp/file.md`
- **THEN** the browser SHALL write the selected-file prompt-ready Markdown to `tmp/file.md` relative to the repository root

### Requirement: Save prompt handles empty and failed writes
The browser SHALL avoid writing files when there is no matching changed-file content and SHALL surface file write failures as status messages.

#### Scenario: Empty visible scope does not write
- **WHEN** the current browser scope has no visible changed files and the user runs `save prompt`
- **THEN** the browser SHALL not create a handoff file
- **AND** the browser SHALL report that there are no changed files to save

#### Scenario: Missing selected file does not write
- **WHEN** the current browser scope has no visible selected changed file and the user runs `save prompt file`
- **THEN** the browser SHALL not create a handoff file
- **AND** the browser SHALL report that there is no changed file to save

#### Scenario: Write failure is reported
- **WHEN** prompt handoff text is generated but the target file cannot be written
- **THEN** the browser SHALL report a file-save failure message without crashing or changing browser state

### Requirement: Save prompt commands are discoverable
The browser command parser and command catalog SHALL expose save prompt commands alongside existing copy prompt commands.

#### Scenario: Commands parse to stable actions
- **WHEN** `save prompt`, `save prompt PATH`, `save prompt file`, or `save prompt file PATH` is parsed
- **THEN** the parser SHALL return stable save-prompt actions with any explicit path captured as the action value

#### Scenario: Command catalog includes save actions
- **WHEN** the command catalog or palette is shown
- **THEN** it SHALL include `save prompt` and `save prompt file` entries
