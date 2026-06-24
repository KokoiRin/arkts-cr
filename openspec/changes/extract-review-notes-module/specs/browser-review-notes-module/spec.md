## ADDED Requirements

### Requirement: Review Notes rules are module-owned
The browser SHALL keep Review Notes summary, filtering, ordering, and copy
message rules in a dedicated UI module.

#### Scenario: Render review notes through module
- **WHEN** the browser needs `notes` or `notes QUERY` output
- **THEN** it SHALL delegate note ordering, filtering, and empty-state text to
  the Review Notes module

#### Scenario: Copy review notes through module
- **WHEN** the browser needs `copy notes` or `copy notes QUERY`
- **THEN** it SHALL delegate rendered text and copy status messages to the
  Review Notes module

### Requirement: Review Notes behavior remains stable
Extracting the module SHALL NOT change user-visible Review Notes behavior.

#### Scenario: Preserve ordering and filtering
- **WHEN** notes are shown or copied
- **THEN** current changed-file notes SHALL remain ordered by changed-file order
- **AND** persisted extra notes SHALL follow sorted by path
- **AND** filtering SHALL remain case-insensitive over path and note text

#### Scenario: Preserve empty states
- **WHEN** there are no notes or no matching filtered notes
- **THEN** the browser SHALL report the same empty-state messages as before
