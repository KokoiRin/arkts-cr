# Command Palette and Help Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

In-session command discovery, executable command palette, page help, and command catalog behavior.

## Requirements
### Requirement: Browser command list entry points
`cr browse` SHALL provide in-session entry points for users to discover command prompt commands.

#### Scenario: Open command list from line mode
- **WHEN** the browser receives `commands`, `cmds`, or `help commands`
- **THEN** the browser SHALL show a command list
- **AND** the session SHALL remain open

#### Scenario: Open command list from raw command prompt
- **WHEN** the browser is in raw-key mode and the user opens `:` command input
- **AND** the user submits empty input or `?`
- **THEN** the browser SHALL show a command list

### Requirement: Browser command list content
The command list SHALL group available browser commands by purpose.

#### Scenario: Show grouped commands
- **WHEN** the command list is shown
- **THEN** it SHALL include navigation commands
- **AND** it SHALL include review scope commands
- **AND** it SHALL include build task commands
- **AND** it SHALL include file/session commands

#### Scenario: Return from command list
- **WHEN** the command list is shown and the user enters `b` or `back`
- **THEN** the browser SHALL return to the changed-file list
- **AND** active build task output SHALL remain available in the bottom task panel

### Requirement: Command palette lists executable commands
`cr browse` SHALL provide an executable command palette in commands mode.

#### Scenario: Open command palette
- **WHEN** the user enters `commands`, `cmds`, or `help commands`
- **THEN** the browser SHALL enter commands mode
- **AND** it SHALL show commands that can be executed directly from the palette

#### Scenario: Non-executable command templates are excluded
- **WHEN** the browser renders the executable command palette
- **THEN** parameter templates such as `base REF` and `range OLD..NEW` SHALL NOT be executable palette rows
- **AND** users SHALL still be able to type those commands through the normal command prompt

### Requirement: Command palette supports keyboard selection
`cr browse` SHALL let raw-key users move within the command palette without changing the selected review file.

#### Scenario: Move selected palette command
- **GIVEN** commands mode is active
- **WHEN** the user presses ↑/↓ or j/k
- **THEN** the selected palette command SHALL move within the executable command list
- **AND** the selected changed file SHALL remain unchanged

#### Scenario: Return to file list
- **GIVEN** commands mode is active
- **WHEN** the user presses b or ←
- **THEN** the browser SHALL return to list mode
- **AND** the selected changed file SHALL remain unchanged

### Requirement: Command palette executes selected commands
`cr browse` SHALL execute the selected palette command when users press Enter in commands mode.

#### Scenario: Execute selected command
- **GIVEN** commands mode is active
- **AND** a palette command is selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute that command through the same command handling path as typed commands

#### Scenario: Enter does not open a file from commands mode
- **GIVEN** commands mode is active
- **AND** the review has visible changed files
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute the selected palette command
- **AND** it SHALL NOT open the selected changed file unless the selected palette command is an explicit file-opening command

### Requirement: Command palette filters executable commands
`cr browse` SHALL allow users to filter executable command palette entries.

#### Scenario: Filter palette commands
- **GIVEN** commands mode is active
- **WHEN** the user enters a command palette filter
- **THEN** the palette SHALL show only executable commands whose group, label, command, or description contains the filter text case-insensitively
- **AND** the selected palette row SHALL clamp to the filtered results

#### Scenario: Empty palette filter result
- **GIVEN** commands mode is active
- **WHEN** the command palette filter matches no executable commands
- **THEN** the palette SHALL show an empty-result message
- **AND** pressing Enter SHALL NOT execute a stale command

### Requirement: Command palette filter is independent from file filter
Command palette search SHALL NOT modify file path filtering.

#### Scenario: Search command palette
- **GIVEN** commands mode is active
- **WHEN** the user presses `/` and enters a command filter
- **THEN** the browser SHALL update the command palette filter
- **AND** it SHALL NOT update the changed-file path filter

#### Scenario: Clear command palette filter
- **GIVEN** commands mode is active
- **AND** the changed-file path filter is set
- **AND** the command palette filter is set
- **WHEN** the user enters `c` or `clear`
- **THEN** the browser SHALL clear the command palette filter
- **AND** it SHALL keep the changed-file path filter unchanged

### Requirement: Task commands are discoverable
The command help and command palette SHALL expose build, test, lint, stop, and rerun commands.

#### Scenario: Open command palette
- **WHEN** the user opens the command palette
- **THEN** executable entries SHALL include build, test, lint, stop, and rerun task actions

### Requirement: File action configuration stays behind file action helpers
The browser SHALL keep command-template parsing and subprocess execution inside `cr.ui.file_actions`.

#### Scenario: Browser executes configured file action
- **WHEN** the browser executes copy or reveal
- **THEN** browser action execution SHALL pass configuration to the file action helper without parsing the template itself

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

### Requirement: Save prompt commands are discoverable
The browser command parser and command catalog SHALL expose save prompt commands alongside existing copy prompt commands.

#### Scenario: Commands parse to stable actions
- **WHEN** `save prompt`, `save prompt PATH`, `save prompt file`, or `save prompt file PATH` is parsed
- **THEN** the parser SHALL return stable save-prompt actions with any explicit path captured as the action value

#### Scenario: Command catalog includes save actions
- **WHEN** the command catalog or palette is shown
- **THEN** it SHALL include `save prompt` and `save prompt file` entries

### Requirement: Page-specific Chinese help
The interactive browser SHALL provide a Help page that explains the currently
active page in Chinese.

#### Scenario: Help opens for the current page
- **GIVEN** the browser is on Task Problems
- **WHEN** the user runs `help`
- **THEN** the browser shows the Help page
- **AND** the Help page describes Task Problems commands in Chinese

#### Scenario: Help preserves navigation
- **GIVEN** the browser opens Help from File Detail
- **WHEN** the user goes back
- **THEN** the browser returns to File Detail with its page state preserved

### Requirement: Chinese visible help surfaces
The interactive browser SHALL show Chinese labels and descriptions for the Help
page, contextual action bar, command palette, and command list.

#### Scenario: Command words remain executable
- **GIVEN** the command list is rendered in Chinese
- **THEN** executable command literals such as `build`, `problems group file`,
  and `copy source` remain unchanged

### Requirement: Filtered palette commands execute normally
Filtered command palette results SHALL execute through the existing command handling path.

#### Scenario: Execute filtered command
- **GIVEN** commands mode is active
- **AND** the command palette filter leaves a matching executable command selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL execute that filtered command
- **AND** it SHALL use the same command handling path as a typed command
