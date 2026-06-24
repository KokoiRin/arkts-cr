## ADDED Requirements

### Requirement: Command palette shows filtered result counts
The browser SHALL show match count feedback when command palette filtering is active.

#### Scenario: Filter has matches
- **WHEN** the command palette filter is `build`
- **THEN** the command palette SHALL show the filter text
- **AND** SHALL show the number of matching executable commands
- **AND** SHALL show the total executable command count

#### Scenario: Filter has no matches
- **WHEN** the command palette filter is `zz-missing`
- **THEN** the command palette SHALL show `0` matching commands
- **AND** SHALL show `No matching commands.`

### Requirement: Command palette ranks stronger matches first
The browser SHALL sort filtered command palette results by match quality while preserving original order for ties.

#### Scenario: Command match outranks description match
- **WHEN** a filter matches one command's command/label and another command's description
- **THEN** the command/label match SHALL appear before the description-only match

### Requirement: Unfiltered command palette order remains stable
The browser SHALL keep the existing palette order when no filter is active.

#### Scenario: No filter
- **WHEN** the command palette has no filter
- **THEN** executable commands SHALL appear in their catalog order
