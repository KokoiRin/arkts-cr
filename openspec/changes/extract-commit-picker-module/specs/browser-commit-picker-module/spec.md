## ADDED Requirements

### Requirement: Commit Picker rules are module-owned
The browser SHALL keep Commit Picker filtering and filtered selection rules in a
dedicated UI module.

#### Scenario: Filter commits through module interface
- **WHEN** browser state or page rendering needs the visible Commit Picker list
- **THEN** it SHALL call the Commit Picker module
- **AND** it SHALL NOT reimplement commit matching in page rendering

#### Scenario: Select from filtered commits
- **WHEN** the user selects a commit while a Commit Picker filter is active
- **THEN** selection SHALL resolve against the module-owned filtered list

### Requirement: Commit Picker module remains pure
The Commit Picker module SHALL NOT own terminal rendering, command parsing, Git
subprocess calls, or browser frame layout.

#### Scenario: Render filtered commits
- **WHEN** Page Content renders Commit Picker rows
- **THEN** Page Content SHALL own the row text
- **AND** the Commit Picker module SHALL only provide commit filtering and
selection facts
