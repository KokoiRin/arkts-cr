## ADDED Requirements

### Requirement: Browser extracts task output problems

The browser SHALL extract lightweight file-location problems from the current task output.

#### Scenario: Extract relative file anchor

- **GIVEN** the current task output contains `src/Foo.ets:12:3`
- **AND** `src/Foo.ets` exists in the repository
- **WHEN** Task Problems are built
- **THEN** the browser SHALL include a problem for `src/Foo.ets` at line `12` and column `3`

#### Scenario: Extract repo absolute file anchor

- **GIVEN** the current task output contains an absolute path under the repository root followed by `:line`
- **WHEN** Task Problems are built
- **THEN** the browser SHALL normalize the problem path to a repo-relative path

#### Scenario: Ignore non-repo anchors

- **GIVEN** the current task output contains a URL, missing file, or absolute path outside the repository
- **WHEN** Task Problems are built
- **THEN** the browser SHALL NOT include a problem for that anchor

### Requirement: Browser shows Task Problems page

The browser SHALL provide a Task Problems page for the current task output.

#### Scenario: Open Task Problems page

- **WHEN** the user runs `problems` or `task problems`
- **THEN** the browser SHALL enter Task Problems page
- **AND** the page SHALL participate in browser back/forward page history
- **AND** selection and scroll SHALL reset when the page opens

#### Scenario: Render Task Problems

- **GIVEN** current task output has extracted problems
- **WHEN** Task Problems page renders
- **THEN** it SHALL show each problem's path, line, optional column, and source output summary

#### Scenario: Render empty state

- **GIVEN** no current task exists or no problem anchors are extracted
- **WHEN** Task Problems page renders
- **THEN** it SHALL show an empty Task Problems state

### Requirement: Browser opens selected task problem

Task Problems page SHALL let users open the selected problem in their editor.

#### Scenario: Open selected problem

- **GIVEN** Task Problems page is visible with at least one problem selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL open the problem path at its line through the existing editor open action
- **AND** it SHALL keep Task Problems page visible

#### Scenario: Navigate task problems

- **GIVEN** Task Problems page is visible with multiple problems
- **WHEN** the user presses movement, paging, home, or end keys
- **THEN** the browser SHALL update problem selection and scroll within valid bounds
