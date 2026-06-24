## ADDED Requirements

### Requirement: Browser shows task preset schema help
The browser SHALL provide a `tasks help` command that explains the supported
`.cr/tasks.json` preset format.

#### Scenario: Show preset format
- **WHEN** the user runs `tasks help`
- **THEN** the browser SHALL show the preset file path
- **AND** SHALL list the supported task keys `build`, `test`, and `lint`
- **AND** SHALL show that each value is a command string
- **AND** SHALL include a compact JSON example
- **AND** SHALL NOT start or stop any task process

### Requirement: Task preset help preserves diagnostics semantics
The browser SHALL keep task source diagnostics and preset format help as
separate commands.

#### Scenario: Show task sources
- **WHEN** the user runs `tasks`
- **THEN** the browser SHALL show command source diagnostics
- **AND** SHALL NOT show the full preset format help

### Requirement: Malformed preset diagnostics point to schema help
Task Runtime SHALL keep malformed `.cr/tasks.json` non-fatal while offering a
concise next step.

#### Scenario: Invalid preset file
- **WHEN** `.cr/tasks.json` is malformed
- **THEN** task diagnostics SHALL include the preset warning
- **AND** SHALL include a hint to run `tasks help`
