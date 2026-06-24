## ADDED Requirements

### Requirement: Task runtime reads project task presets
The system SHALL read project-local task presets from `.cr/tasks.json` at the repository root.

#### Scenario: Resolve task command from preset
- **WHEN** `.cr/tasks.json` contains a string command for `build`, `test`, or `lint`
- **THEN** the task runtime SHALL use that command when no CLI argument or environment variable overrides the same task kind

#### Scenario: Ignore invalid preset file
- **WHEN** `.cr/tasks.json` is missing, invalid JSON, not a JSON object, or contains a non-string value for a task kind
- **THEN** the task runtime SHALL ignore the invalid preset data and continue resolving commands from the remaining existing sources

### Requirement: Task command precedence remains explicit
The system SHALL resolve task commands using the precedence CLI argument, environment variable, project preset, DouyinHarmony build default, missing-command fallback.

#### Scenario: CLI argument overrides preset
- **WHEN** a task command is provided by CLI argument and `.cr/tasks.json` also contains that task kind
- **THEN** the CLI argument SHALL be used

#### Scenario: Environment variable overrides preset
- **WHEN** a task command is provided by environment variable and `.cr/tasks.json` also contains that task kind
- **THEN** the environment variable SHALL be used

#### Scenario: DouyinHarmony default remains build fallback
- **WHEN** the task kind is `build`, no CLI argument, environment variable, or project preset is present, and the repository is DouyinHarmony with `remote`
- **THEN** the existing DouyinHarmony build command SHALL be used

### Requirement: Browser task behavior remains compatible
The browser SHALL continue to use build/test/lint commands through Task Runtime without changing task panel rendering or command interaction.

#### Scenario: Existing task commands use presets transparently
- **WHEN** users run `build`, `test`, or `lint` in raw-key or line mode
- **THEN** the browser SHALL use the resolved task command from Task Runtime and preserve foreground/background behavior
