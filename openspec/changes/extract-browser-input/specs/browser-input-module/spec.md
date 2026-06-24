## ADDED Requirements

### Requirement: Browser Input Module Ownership

`cr browse` terminal input protocol MUST be owned by a dedicated UI module rather than browser session orchestration.

#### Scenario: Browser reads commands through Browser Input

- **GIVEN** an interactive browser session in raw-key or line mode
- **WHEN** the browser waits for the next command or temporary query
- **THEN** terminal input details such as raw-key detection, command reading, query reading, raw escape parsing, and EOF/interrupt/tick sentinels are provided by the Browser Input module
- **AND** browser orchestration remains responsible for interpreting returned command text, mutating state, restoring the Browser Frame, saving workspace state, and executing commands

### Requirement: Browser Input Behavior Preservation

Extracting Browser Input MUST preserve existing user-visible input behavior.

#### Scenario: Existing input tokens stay stable

- **GIVEN** the same stdin/stdout TTY state, raw-key bytes, line input, EOF, KeyboardInterrupt, and idle timeout as before extraction
- **WHEN** browser input is read
- **THEN** returned command tokens remain behaviorally equivalent, including `__tick__`, `__eof__`, `__interrupt__`, `filter_prompt`, `command_prompt`, arrow navigation, paging, home/end, vim-style movement keys, space, and ordinary character commands
- **AND** normal raw-key reads do not print an extra newline
- **AND** temporary prompt cancellation still lets the browser run loop force a full redraw
