## ADDED Requirements

### Requirement: Parsed command actions execute through one action execution interface
The system SHALL execute parsed browser command actions through a dedicated action execution interface instead of keeping every action branch directly in `run_browser`.

#### Scenario: Run loop delegates executable actions
- **WHEN** `run_browser` has resolved temporary prompt input and parsed a browser command
- **THEN** it SHALL call the action execution interface with the parsed command and use the returned loop control result

#### Scenario: Executor reports redraw needs
- **WHEN** an action changes visible browser state
- **THEN** the execution interface SHALL return a result that asks the run loop to redraw

#### Scenario: Executor reports quit intent
- **WHEN** the parsed command is quit
- **THEN** the execution interface SHALL return an exit code and the run loop SHALL remain responsible for saving workspace state before returning that code

### Requirement: Action execution preserves existing behavior
The system SHALL preserve the existing browser command behavior while moving execution behind the action execution interface.

#### Scenario: Scope and navigation actions behave as before
- **WHEN** users run existing scope or navigation commands such as `staged`, `all`, `base REF`, `range OLD..NEW`, `g`, `b`, `enter`, `n`, or `p`
- **THEN** the same review scope, page, selection, and redraw behavior SHALL be preserved

#### Scenario: Task actions behave as before
- **WHEN** users run existing task commands such as `build`, `test`, `lint`, `stop`, or `rerun`
- **THEN** the same foreground or background task behavior SHALL be preserved for line mode and raw-key mode

#### Scenario: Unknown command feedback behaves as before
- **WHEN** users enter an unknown command
- **THEN** the same raw-key or line-mode feedback text SHALL be produced through the browser feedback path

### Requirement: Input prompt protocol remains outside normal action execution
The system SHALL keep temporary input prompt handling at the run loop input edge.

#### Scenario: Filter prompt is resolved before normal execution
- **WHEN** the parsed command requests the filter prompt
- **THEN** the run loop SHALL read the filter query, update the correct filter, and not route the prompt action through normal action execution

#### Scenario: Command prompt is resolved before normal execution
- **WHEN** the parsed command requests the command prompt
- **THEN** the run loop SHALL read and normalize the command query, parse the resulting command, and then route only the resulting executable action through normal action execution
