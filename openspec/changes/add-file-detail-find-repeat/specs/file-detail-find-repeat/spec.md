## ADDED Requirements

### Requirement: Repeat File Detail text search
The browser SHALL let users repeat the most recent File Detail text search
within the current rendered file.

#### Scenario: Move to next match
- **WHEN** the user has run `find TEXT` in File Detail
- **AND** the user runs `next match`
- **THEN** the browser SHALL jump to the next rendered body line containing
  `TEXT` case-insensitively
- **AND** it SHALL wrap to the first match when already at or after the last
  match

#### Scenario: Move to previous match
- **WHEN** the user has run `find TEXT` in File Detail
- **AND** the user runs `prev match`
- **THEN** the browser SHALL jump to the previous rendered body line containing
  `TEXT` case-insensitively
- **AND** it SHALL wrap to the last match when already at or before the first
  match

#### Scenario: No prior find query
- **WHEN** the user runs `next match` or `prev match` before `find TEXT`
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that `find TEXT` must run first

#### Scenario: Stored query no longer matches
- **WHEN** the user runs `next match` or `prev match`
- **AND** the stored query no longer matches the current rendered File Detail
- **THEN** the browser SHALL keep the current page and scroll
- **AND** it SHALL report that no match was found
