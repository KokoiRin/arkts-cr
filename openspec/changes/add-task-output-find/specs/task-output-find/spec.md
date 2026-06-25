## ADDED Requirements

### Requirement: Task Output page finds current output text

Task Output Page SHALL support text search over the current task's captured output.

#### Scenario: Find text in task output

- **GIVEN** Task Output Page is visible
- **AND** the current task output contains a line matching the query
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL store `TEXT` as the task output find query
- **AND** scroll Task Output Page to the first matching output line
- **AND** show status feedback for the match

#### Scenario: Find is case-insensitive and ignores ANSI style

- **GIVEN** Task Output Page is visible
- **AND** the current task output contains styled text whose plain form matches the query with different casing
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL treat that line as a match

#### Scenario: Find without current task

- **GIVEN** Task Output Page is visible
- **AND** no current task exists
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL keep the page and report that there is no task output to find

### Requirement: Task Output page repeats find matches

Task Output Page SHALL support repeat navigation for the most recent non-empty task output find query.

#### Scenario: Next and previous task output match

- **GIVEN** Task Output Page is visible
- **AND** a task output find query has been stored
- **WHEN** the user runs `next match` or `prev match`
- **THEN** the browser SHALL move to the next or previous matching output line with wraparound
- **AND** keep File Detail find state unchanged

#### Scenario: Repeat find without task output query

- **GIVEN** Task Output Page is visible
- **AND** no task output find query has been stored
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL report `Run find TEXT first.`

### Requirement: File Detail find behavior remains stable

Extracting shared rendered-text search SHALL preserve File Detail find behavior.

#### Scenario: File Detail find still searches rendered detail text

- **GIVEN** File Detail is visible
- **WHEN** the user runs `find TEXT`, `next match`, or `prev match`
- **THEN** the browser SHALL keep the same File Detail messages, scroll behavior, and `file_find_text` behavior as before
