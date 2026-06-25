## ADDED Requirements

### Requirement: Browser opens source preview from task problem

The browser SHALL provide a read-only Source File Page for the selected Task Problems entry.

#### Scenario: View selected problem source

- **GIVEN** Task Problems Page is visible with a selected problem
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL enter Source File Page for that problem's repo-local path
- **AND** it SHALL mark the problem line
- **AND** the previous Task Problems Page SHALL be reachable through browser back history

#### Scenario: Preserve external editor enter behavior

- **GIVEN** Task Problems Page is visible
- **WHEN** the user presses Enter
- **THEN** the browser SHALL continue to open the selected problem through the existing external editor action

#### Scenario: No selected problem

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL report that no task problem can be viewed
- **AND** it SHALL keep the current page visible

### Requirement: Browser renders source file page

Source File Page SHALL render source text with line numbers.

#### Scenario: Render target line

- **GIVEN** Source File Page has a readable repo-local text file and target line
- **WHEN** the page renders
- **THEN** it SHALL show the repo-relative path
- **AND** it SHALL show line-numbered source rows
- **AND** it SHALL mark the target line

#### Scenario: Scroll source file

- **GIVEN** Source File Page is visible
- **WHEN** the user presses movement, paging, home, or end keys
- **THEN** the browser SHALL update source scroll within valid bounds

#### Scenario: Render unreadable source

- **GIVEN** Source File Page references a missing or unreadable file
- **WHEN** the page renders
- **THEN** it SHALL show a clear source-file empty/error state
