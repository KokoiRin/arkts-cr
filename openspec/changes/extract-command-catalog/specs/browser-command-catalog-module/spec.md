## ADDED Requirements

### Requirement: Browser command catalog module owns command surface data
The browser SHALL use a dedicated UI module for command catalog data, executable palette entries, command filtering, and command command-surface line rendering.

#### Scenario: Command catalog exposes grouped commands
- **WHEN** code asks for the browser command catalog
- **THEN** the module SHALL return the existing command groups in their existing order
- **AND** command labels, descriptions, and executable actions SHALL remain unchanged

#### Scenario: Executable palette entries exclude placeholders
- **WHEN** code asks for command palette entries
- **THEN** the module SHALL include executable commands such as `build`, `copy path`, and `copy prompt`
- **AND** SHALL exclude non-executable placeholder entries such as `base REF`, `note TEXT`, and `copy notes QUERY`

#### Scenario: Command palette filtering preserves ranking
- **WHEN** code filters command palette entries
- **THEN** exact and prefix command/label matches SHALL rank before group matches
- **AND** group matches SHALL rank before description-only matches
- **AND** stable catalog order SHALL break ties

#### Scenario: Browser preserves command palette behavior
- **WHEN** the browser renders the command list or command palette
- **THEN** the output SHALL preserve the existing command text, match counts, empty state, selection marker, and clipped-window behavior
- **AND** the browser SHALL keep owning command selection, command filter text, and command scroll state
