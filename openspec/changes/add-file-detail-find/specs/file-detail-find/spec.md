## ADDED Requirements

### Requirement: Find rendered text in File Detail
The browser SHALL let users jump to rendered text inside the current File
Detail page.

#### Scenario: Find matching rendered text
- **WHEN** the user runs `find TEXT` in File Detail
- **AND** a rendered File Detail body line contains `TEXT` case-insensitively
- **THEN** the browser SHALL set File Detail scroll to the first matching body
  line
- **AND** it SHALL keep the current Review Scope, selected file, notes,
  progress, and task state

#### Scenario: No matching rendered text
- **WHEN** the user runs `find TEXT` in File Detail
- **AND** no rendered body line contains `TEXT`
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that no match was found

#### Scenario: Empty query
- **WHEN** the user runs `find` or `find   `
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that a search query is required

#### Scenario: Find outside File Detail
- **WHEN** the user runs `find TEXT` outside File Detail
- **THEN** the browser SHALL keep the current page
- **AND** it SHALL report that a file detail must be opened first
