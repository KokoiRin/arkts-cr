## ADDED Requirements

### Requirement: Browser navigation owns page transition rules
The browser SHALL route page transition rules through a dedicated navigation module instead of scattering raw page assignments through the main browse loop.

#### Scenario: Navigation opens changed files
- **WHEN** the browser returns to Changed Files from another page
- **THEN** the current page SHALL become Changed Files
- **AND** file detail scroll SHALL reset

#### Scenario: Navigation opens file detail
- **WHEN** the browser opens File Detail for the selected changed file
- **THEN** the current page SHALL become File Detail
- **AND** file detail scroll SHALL reset

#### Scenario: Navigation opens cross-layer pages
- **WHEN** the browser opens Scope Home, Commit Picker, or Command Palette
- **THEN** the current page SHALL match the requested page
- **AND** page-local selection or scroll SHALL reset where existing behavior already resets it

### Requirement: Existing browser navigation behavior remains stable
Introducing the navigation module SHALL preserve the existing user-visible browse behavior.

#### Scenario: Back behavior remains hierarchy-aware
- **WHEN** the user goes back from Command Palette, Scope Home, or File Detail
- **THEN** the browser SHALL return to Changed Files
- **AND** file detail scroll SHALL reset

#### Scenario: Selected commit back behavior remains compatible
- **WHEN** the user is in a selected commit scope and goes back from Changed Files
- **THEN** the browser SHALL return to Commit Picker as before

#### Scenario: Persistence remains compatible
- **WHEN** browser workspace state is saved or restored
- **THEN** persisted `mode` values SHALL remain the existing string values
