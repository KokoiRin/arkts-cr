# Workbench Architecture Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Module ownership and locality contracts that keep product behavior maintainable.

## Requirements
### Requirement: Browser module locality
Interactive browse behavior SHALL be owned by a dedicated browser module instead of the CLI argument parsing module.

#### Scenario: CLI dispatches to browser module
- **WHEN** the `browse` command is invoked
- **THEN** the CLI delegates browser execution to the browser module through a small function interface
- **AND** browse state transitions and rendering are implemented outside the CLI parser module

### Requirement: Existing browser behavior remains stable
Adding the page model SHALL preserve existing user-visible behavior.

#### Scenario: Existing prompts and persistence
- **WHEN** the browser renders prompts or saves workspace state
- **THEN** it SHALL keep the existing prompt strings and persisted mode values

#### Scenario: Existing navigation
- **WHEN** the user navigates between scope home, commit picker, changed files, file detail, and command palette
- **THEN** behavior SHALL remain the same as before the page model

### Requirement: Browser commands parse to stable actions
The browser SHALL parse command input into stable command actions before executing browser behavior.

#### Scenario: Alias commands map to the same action
- **WHEN** the parser receives aliases such as `q`, `quit`, or `exit`
- **THEN** it SHALL return the same quit action

#### Scenario: Parameter commands expose values
- **WHEN** the parser receives `base REF`, `range OLD..NEW`, `filter QUERY`, `/QUERY`, or a numeric choice
- **THEN** it SHALL return the matching action
- **AND** it SHALL expose the parsed value without requiring the execution layer to parse the raw string again

#### Scenario: Unknown commands remain explicit
- **WHEN** the parser receives an unsupported command
- **THEN** it SHALL return an unknown action
- **AND** the browser SHALL keep existing unknown-command feedback behavior

### Requirement: Existing browser command behavior remains stable
Introducing command dispatch SHALL preserve existing user-visible behavior.

#### Scenario: Existing commands still execute
- **WHEN** the user runs existing navigation, scope, task, filter, progress, file, and session commands
- **THEN** they SHALL behave as before command dispatch deepening

#### Scenario: Raw-key prompt sentinels remain browser-owned
- **WHEN** the command reader returns tick, eof, or interrupt sentinels
- **THEN** the browser loop SHALL keep existing lifecycle handling
- **AND** command dispatch SHALL NOT replace task-panel tick or clean-exit behavior

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

### Requirement: Browser task behavior remains compatible
The browser SHALL continue to use build/test/lint commands through Task Runtime without changing task panel rendering or command interaction.

#### Scenario: Existing task commands use presets transparently
- **WHEN** users run `build`, `test`, or `lint` in raw-key or line mode
- **THEN** the browser SHALL use the resolved task command from Task Runtime and preserve foreground/background behavior

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

### Requirement: Browser keeps page rendering orchestration
The browser SHALL continue to own page-specific main content generation, command execution, prompt input flow, and workspace save/restore orchestration while delegating Browser Frame and Task Panel presentation implementation to the frame module.

#### Scenario: Browser wrappers preserve existing behavior
- **WHEN** existing browser helper entry points such as `_screen_layout`, `_task_panel_lines`, `_draw_task_panel_only`, and `_fit_terminal_line` are called
- **THEN** they SHALL return the same observable results through delegation to the Browser Frame module

### Requirement: Page Content Module Ownership

`cr browse` page-specific main content rendering MUST be owned by a dedicated UI module rather than browser session orchestration.

#### Scenario: Browser renders through Page Content

- **GIVEN** an interactive browser state on Scope Home, Commit Picker, Changed Files, or File Detail
- **WHEN** the browser draws the main content area
- **THEN** page-specific text such as scope options, commit rows, changed-file tree rows, empty states, and file detail lines is generated by the Page Content module
- **AND** Browser Frame remains responsible for screen placement and Task Panel presentation
- **AND** browser orchestration remains responsible for input, command execution, workspace startup/exit, and selected-file side effects

### Requirement: Page Content Behavior Preservation

Extracting Page Content MUST preserve existing user-visible browser page behavior.

#### Scenario: Existing pages keep the same visible output

- **GIVEN** the same browser state, CLI args, terminal style, and terminal height as before extraction
- **WHEN** Scope Home, Commit Picker, Changed Files, empty Changed Files, or File Detail content is rendered
- **THEN** prompts, help text, breadcrumbs, changed-file tree styling, progress lines, note markers, commit rows, file detail headers, risk/purpose/symbol lines, hunk lines, and scroll footers remain behaviorally equivalent
- **AND** list, commit, command, and file scroll offsets are still clamped to the visible window

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
