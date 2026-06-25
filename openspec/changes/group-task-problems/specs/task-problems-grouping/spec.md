## ADDED Requirements

### Requirement: Browser groups Task Problems by file

The browser SHALL support page-local file grouping for current Task Problems.

#### Scenario: Enable file grouping

- **GIVEN** Task Problems has visible problems from multiple files
- **WHEN** the user runs `problems group file`
- **THEN** the Task Problems page SHALL render file headers before each file's
  problem rows
- **AND** the page header SHALL show that grouping is active.

#### Scenario: Disable grouping

- **GIVEN** Task Problems is grouped by file
- **WHEN** the user runs `problems group none`
- **THEN** the Task Problems page SHALL render the flat problem list.

### Requirement: Grouping composes with visible problem actions

Task Problems grouping SHALL NOT change the visible problem list used by
selection and problem actions.

#### Scenario: Actions use visible problem list

- **GIVEN** Task Problems has grouping enabled
- **WHEN** the user opens, views, copies, or saves context for a selected problem
- **THEN** the action SHALL use the same filtered, queried, and sorted visible
  `TaskProblem` list as flat mode.

#### Scenario: Page history restores grouping

- **GIVEN** Task Problems has grouping enabled
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active grouping mode SHALL be restored.
