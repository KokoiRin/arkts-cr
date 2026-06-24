## ADDED Requirements

### Requirement: Browser shows task command diagnostics
The browser SHALL provide a `tasks` command that reports command sources for build, test, and lint.

#### Scenario: Show task sources
- **WHEN** the user runs `tasks`
- **THEN** the browser SHALL show source diagnostics for `build`, `test`, and `lint`
- **AND** SHALL NOT start or stop any task process

### Requirement: Task runtime explains command precedence
Task Runtime SHALL explain the winning task command source using the existing precedence CLI argument, environment variable, project preset, DouyinHarmony build default, missing.

#### Scenario: CLI, env, preset, default, and missing sources
- **WHEN** different task kinds are configured from different command sources
- **THEN** diagnostics SHALL identify the winning source for each task kind

### Requirement: Preset parsing diagnostics are non-fatal
Task Runtime SHALL report malformed `.cr/tasks.json` in diagnostics while preserving tolerant command resolution.

#### Scenario: Invalid preset file
- **WHEN** `.cr/tasks.json` is malformed
- **THEN** diagnostics SHALL include a preset warning
- **AND** command resolution SHALL continue to use other available sources
