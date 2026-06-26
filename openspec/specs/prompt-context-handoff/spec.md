# Prompt and Context Handoff Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Prompt, diff, source, problem, task-output, and review-note handoff packages.

## Requirements
### Requirement: Browser copies prompt handoff
The browser SHALL provide commands that copy prompt-ready Markdown for the current review context to the configured clipboard action.

#### Scenario: Copy current visible scope prompt with review notes
- **WHEN** the user runs `copy prompt`
- **AND** visible changed files have review notes in the current Review Workspace
- **THEN** the copied prompt SHALL include matching review notes for those visible files
- **AND** SHALL NOT include review notes for files outside the copied visible file set
- **AND** the browser SHALL keep the current page, selection, Review Scope, file filter, progress markers, review notes, and task state unchanged

#### Scenario: Copy selected file prompt with review note
- **WHEN** the user runs `copy prompt file`
- **AND** the selected visible changed file has a review note
- **THEN** the copied prompt SHALL include that review note
- **AND** SHALL NOT include review notes for other files

### Requirement: Save current visible prompt handoff
The browser SHALL support `save prompt [PATH]` to write prompt-ready Markdown for the current visible changed files to a file.

#### Scenario: Save visible scope to default path
- **WHEN** the current browser scope has visible changed files and the user runs `save prompt`
- **THEN** the browser SHALL write the same prompt-ready Markdown used by `copy prompt` to `.cr/handoff/review-prompt.md`
- **AND** the browser SHALL report the saved repo-relative path without changing page, selection, Review Scope, file filter, progress markers, review notes, or task state

#### Scenario: Save visible scope to explicit path
- **WHEN** the current browser scope has visible changed files and the user runs `save prompt tmp/review.md`
- **THEN** the browser SHALL write the prompt-ready Markdown to `tmp/review.md` relative to the repository root

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

### Requirement: Keep task tail handoff lightweight

Task output tail handoff MUST NOT change task lifecycle, task history, Problems parsing, task output capture capacity, or workspace persistence.

#### Scenario: Tail handoff is a snapshot
- **GIVEN** a task is still running
- **WHEN** the user copies or saves task output tail
- **THEN** the handoff SHALL use the currently captured output snapshot
- **AND** the task SHALL continue running normally
