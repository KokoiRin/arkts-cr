# TUI Frame and Navigation Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Terminal frame regions, raw-key input, page model, breadcrumbs, navigation history, and redraw rules.

## Requirements
### Requirement: Input prompt protocol remains outside normal action execution
The system SHALL keep temporary input prompt handling at the run loop input edge.

#### Scenario: Filter prompt is resolved before normal execution
- **WHEN** the parsed command requests the filter prompt
- **THEN** the run loop SHALL read the filter query, update the correct filter, and not route the prompt action through normal action execution

#### Scenario: Command prompt is resolved before normal execution
- **WHEN** the parsed command requests the command prompt
- **THEN** the run loop SHALL read and normalize the command query, parse the resulting command, and then route only the resulting executable action through normal action execution

### Requirement: Browser screen regions
`cr browse` SHALL render interactive TTY sessions using stable screen regions for content, background task output, and command input.

#### Scenario: Render with no background task
- **WHEN** the browser has no active build panel
- **THEN** the main content region SHALL use the available terminal rows above the input prompt
- **AND** the input prompt SHALL remain on the final terminal row

#### Scenario: Render with a build panel
- **WHEN** a build panel is present
- **THEN** the main content region SHALL shrink to leave room for the build panel
- **AND** the build panel SHALL render above the input prompt
- **AND** the input prompt SHALL remain below the build panel

### Requirement: Raw-key commands do not scroll the screen
`cr browse` SHALL treat raw-key input as command events instead of terminal text output.

#### Scenario: User presses a navigation key
- **WHEN** raw-key mode reads a navigation key, selection key, or page key
- **THEN** command reading SHALL NOT print an extra newline
- **AND** the next visible change SHALL come from fixed-area redraw or isolated panel refresh

#### Scenario: User enters line input intentionally
- **WHEN** the user opens filter input or command input
- **THEN** the browser MAY show a dedicated line prompt for that input
- **AND** returning from that input SHALL restore fixed-region rendering on the next redraw

### Requirement: Task-panel partial refresh is frame-safe
`cr browse` SHALL only perform task-panel partial refreshes when the last complete frame still matches the current screen layout.

#### Scenario: Task output changes with a valid frame
- **GIVEN** a complete browser frame has been rendered
- **AND** the current layout matches that frame
- **WHEN** build output changes while the user is idle
- **THEN** the browser SHALL update only the task-panel rows
- **AND** it SHALL preserve the command prompt cursor position
- **AND** it SHALL NOT clear the full screen

#### Scenario: Task output changes without a valid frame
- **GIVEN** no complete frame exists or the layout has changed since the last frame
- **WHEN** build output changes while the user is idle
- **THEN** the browser SHALL NOT write a partial task-panel update
- **AND** it SHALL request a full browser frame redraw

#### Scenario: Task output is unchanged
- **GIVEN** a complete browser frame has been rendered
- **WHEN** the task-panel text is unchanged
- **THEN** the browser SHALL NOT write a duplicate task-panel update

### Requirement: Temporary line input restores fixed frame
`cr browse` SHALL restore the fixed browser frame after temporary command or filter line input.

#### Scenario: Command prompt returns
- **WHEN** the user opens `:` command input and submits or cancels it
- **THEN** the browser SHALL mark the frame dirty
- **AND** the next raw-key visual update SHALL be a full browser frame redraw

#### Scenario: Filter prompt returns
- **WHEN** the user opens `/` filter input and submits or cancels it
- **THEN** the browser SHALL mark the frame dirty
- **AND** the next raw-key visual update SHALL be a full browser frame redraw

### Requirement: Browser uses explicit page layers
`cr browse` raw-key mode SHALL render the screen as a single frame composed of context/status, main content, background task panel, and input prompt layers.

#### Scenario: Full redraw with a running task
- **GIVEN** a background build exists
- **WHEN** the browser performs a full redraw
- **THEN** it SHALL render context/status above the main content
- **AND** it SHALL render the task panel above the final prompt row
- **AND** it SHALL place the prompt on the final terminal row

### Requirement: Raw-key feedback stays inside the browser frame
Raw-key browser actions SHALL NOT print ordinary feedback outside the fixed frame.

#### Scenario: Open selected file in raw-key mode
- **WHEN** the user opens a selected file
- **THEN** the browser SHALL show the result in the context/status layer
- **AND** it SHALL schedule a full redraw
- **AND** it SHALL NOT append feedback below the prompt

#### Scenario: Invalid selection in raw-key mode
- **WHEN** the user enters an invalid numeric selection
- **THEN** the browser SHALL show the validation message in the context/status layer
- **AND** it SHALL schedule a full redraw

#### Scenario: Unknown command in raw-key mode
- **WHEN** the user enters an unknown command
- **THEN** the browser SHALL show a compact unknown-command message in the context/status layer
- **AND** it SHALL schedule a full redraw

### Requirement: Browser context renders product navigation breadcrumbs
`cr browse` SHALL render the product navigation hierarchy in the context/status layer.

#### Scenario: Changed Files layer
- **GIVEN** the browser is showing the changed-file tree for a Review Scope
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: <scope> > Files`

#### Scenario: File Detail layer
- **GIVEN** the browser is showing a selected file detail
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: <scope> > Files > <path>`

#### Scenario: Commit picker layer
- **GIVEN** the browser is showing recent commits before a commit is selected
- **WHEN** the screen is redrawn
- **THEN** the context/status layer SHALL show `Scope: recent commits`
- **AND** it SHALL NOT append `> Files`

#### Scenario: Selected commit files
- **GIVEN** the user selected a commit as the Review Scope
- **WHEN** the browser shows that commit's changed-file tree
- **THEN** the context/status layer SHALL show `Scope: commit <short-sha> > Files`

#### Scenario: Status message
- **GIVEN** a raw-key action has produced a status message
- **WHEN** the context/status layer is rendered
- **THEN** the status message SHALL appear after the breadcrumb

### Requirement: Browser exposes an explicit page model
The browser SHALL expose explicit page names for the existing product pages.

#### Scenario: Page names exist
- **WHEN** maintainers inspect the browser page model
- **THEN** it SHALL include named pages for scope home, commit picker, changed files, file detail, and command palette
- **AND** those names SHALL map to the existing persisted/prompt string values

#### Scenario: Browser state owns current page
- **WHEN** a new browser state is created
- **THEN** its current page SHALL be Changed Files
- **AND** `mode` compatibility SHALL read and write the same current page

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

### Requirement: 页面展示上下文动作条
系统 SHALL 在 raw-key `cr browse` frame 中展示一行与当前页面相关的高频动作提示。

#### Scenario: Changed Files 动作条
- **WHEN** 用户位于 Changed Files 页面
- **THEN** frame SHALL 展示包含打开文件、过滤、标记已看、done-next、任务和命令面板入口的动作条

#### Scenario: File Detail 动作条
- **WHEN** 用户位于 File Detail 页面
- **THEN** frame SHALL 展示包含 hunk/change 导航、查找、打开/复制当前位置、done-next 和返回文件列表的动作条

#### Scenario: Scope Home 动作条
- **WHEN** 用户位于 Scope Home 页面
- **THEN** frame SHALL 展示包含选择 scope、返回、recent commits、base/range 命令和命令面板入口的动作条

#### Scenario: Commit Picker 动作条
- **WHEN** 用户位于 Commit Picker 页面
- **THEN** frame SHALL 展示包含选择 commit、过滤 commit、清除过滤、返回和命令面板入口的动作条

#### Scenario: Command Palette 动作条
- **WHEN** 用户位于 Command Palette 页面
- **THEN** frame SHALL 展示包含执行命令、搜索命令、清除搜索和返回的动作条

### Requirement: 动作条保持 frame 布局稳定
系统 MUST 将上下文动作条作为 main content 的一部分渲染，并保持 prompt 与 Task Panel 区域稳定。

#### Scenario: Task Panel 运行时
- **WHEN** 后台 task 正在运行并触发 raw-key full redraw
- **THEN** frame SHALL 仍保留 Task Panel 区域并在主内容区域内展示动作条

#### Scenario: 终端宽度不足
- **WHEN** 动作条文本超过终端宽度
- **THEN** frame SHALL 截断动作条单行文本而不是让它换行破坏布局

### Requirement: 动作条不改变命令行为
系统 MUST 只展示已有命令提示，不改变命令解析、workspace state 或持久化 schema。

#### Scenario: Existing command parsing
- **WHEN** 用户输入已有命令或快捷键
- **THEN** command parser SHALL 返回与引入动作条之前相同的 BrowserCommandAction

#### Scenario: Workspace persistence
- **WHEN** 浏览器保存 workspace state
- **THEN** persisted data SHALL NOT include contextual action bar state

### Requirement: Browse non-TTY compatibility
`cr browse` SHALL preserve line-oriented operation when stdin or stdout is not an interactive TTY.

#### Scenario: Filter from line mode
- **WHEN** `cr browse` runs in non-TTY mode and receives `/query` or `filter query`
- **THEN** the browser applies the query as a path filter
- **AND** subsequent line-mode selections operate on the filtered file list

#### Scenario: Existing line-mode commands keep working
- **WHEN** `cr browse` runs in non-TTY mode
- **THEN** existing commands for list, numeric selection, next, previous, refresh, open, help, and quit continue to work

### Requirement: Browser frame owns raw-key screen rendering
`cr browse` SHALL coordinate raw-key full redraws, task-panel partial refreshes, and prompt placement through a single browser frame state.

#### Scenario: Full redraw records the current frame
- **WHEN** raw-key browser mode performs a full screen redraw
- **THEN** the browser SHALL record the layout used for that redraw
- **AND** it SHALL record that a complete frame exists
- **AND** it SHALL record the task-panel contents rendered in that frame

#### Scenario: User command redraw replaces the previous frame
- **WHEN** a user command changes selection, mode, scope, filter, or scroll state
- **THEN** the next visible update SHALL be a full browser frame redraw
- **AND** any later partial task-panel refresh SHALL use the latest frame layout

### Requirement: Task panel partial refresh respects frame ownership
Background task partial refresh SHALL only write to the task panel when the existing browser frame is complete and still owns the terminal layout.

#### Scenario: Frame is incomplete or dirty
- **GIVEN** the browser frame is incomplete or dirty
- **WHEN** build output changes
- **THEN** the task panel partial refresh SHALL refuse to write
- **AND** the browser SHALL perform a later full redraw

#### Scenario: Status message is pending
- **GIVEN** a raw-key action has produced a status message that has not been rendered by a full redraw
- **WHEN** build output changes
- **THEN** the task panel partial refresh SHALL refuse to write over the stale frame

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

### Requirement: Browser Frame module owns screen-region layout
The system SHALL provide a Browser Frame rendering module that owns terminal height measurement, prompt row calculation, main-content height calculation, task-panel height calculation, and task-panel start-row calculation.

#### Scenario: Layout reserves prompt and task panel regions
- **WHEN** a background task is present on a 12-row terminal
- **THEN** the Browser Frame module SHALL reserve the final row for the prompt and place the task panel above it without consuming the main content region entirely

#### Scenario: Layout without task keeps prompt at bottom
- **WHEN** no background task is present on a 12-row terminal
- **THEN** the Browser Frame module SHALL reserve the final row for the prompt and give the remaining rows to main content
