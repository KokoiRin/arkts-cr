# Workbench navigation model

`cr` 的长期产品目标是 terminal workbench：把日常 IDE 里的高频 review、导航、构建和仓库操作收进一个稳定的终端界面。这个文件定义产品导航层级，后续实现应优先服从这里的模型。

## Two Different Layers

`cr browse` 有两套“层”，不要混用。

**Product navigation layers**

这是用户心智里的层级，回答“我现在在看什么对象”。

```text
Review Scope
  -> Changed Files
    -> File Detail
```

**Screen rendering layers**

这是终端屏幕里的区域所有权，回答“谁能写哪几行”。

```text
context/status
main content
background task panel
input prompt
```

屏幕渲染层服务产品导航层，但不能替代产品导航层。比如 bottom build panel 属于屏幕渲染层；它不应该成为用户在 review 层级里的一个“页面”。

## Canonical Product Hierarchy

### 1. Review Scope

Review Scope 是一级对象：它定义当前要 review 的变化集合。

当前 scope 类型：

- `worktree`: 未提交工作区改动。
- `staged`: index / staged 改动。
- `all local changes`: staged + unstaged 的本地改动集合。
- `base REF`: 当前工作区相对某个 base ref 的变化。
- `range OLD..NEW`: 两个 ref 之间的显式变化范围。
- `commit <sha>`: 某一个历史 commit 的变化。

Commit 不应该是和文件平铺在一起的普通 mode。它是 Review Scope 的一种 adapter：选中 commit 后，产品上进入 `commit <sha>` scope；随后仍然进入 Changed Files 层。

一级页面未来应更像 workspace/scope home，而不只是现在的 `g` recent commits 列表。它应该让用户清楚看到自己可以进入哪些变化集合。

Scope Home counts 属于这一层的临时概览：它告诉用户 Worktree、Staged、All local changes、Recent commits 当前各有多少内容，但不改变 Review Scope，也不进入持久 workspace state。

### 2. Changed Files

Changed Files 是二级对象：它展示当前 Review Scope 里改动了哪些文件。

这层负责：

- 文件树和路径层级。
- 每个文件的 added/deleted 统计。
- 文件状态：modified、added、deleted、renamed、untracked。
- 本地 change source：staged、unstaged、mixed。
- source 过滤：source staged、source unstaged、source mixed、source all。
- source 统计：当前 Changed Files 里 staged、unstaged、mixed 的可见数量。
- 轻量 review 进度：seen/todo、remaining。
- 轻量 per-file note 标记。
- 路径过滤和排序。

这层不负责展示完整 diff。它的目标是帮助用户理解“这个 scope 改了哪些地方，以及我下一步应该进哪个文件”。

### 3. File Detail

File Detail 是三级对象：它展示某个文件在当前 Review Scope 中的具体变化。

这层负责：

- 单文件 diff hunks。
- old/new 行号。
- first changed line anchor。
- changed symbols。
- purpose hint。
- review note。
- 打开外部编辑器。
- 在当前 scope 的文件之间 next/previous。

这层必须始终知道自己属于哪个 Review Scope 和哪个 Changed Files 集合。`back` 优先返回 in-session page stack 中的上一页；没有历史时再使用产品层级 fallback，例如从 File Detail 返回 Changed Files。

## Persistent Navigation Terms

后续代码、文档和测试优先使用这些词：

- `Review Scope`: 当前 review 的变化集合。
- `Changed Files`: 某个 scope 下的文件树/文件列表层。
- `File Detail`: 某个文件的具体 diff/outline/detail 层。
- `Command Palette`: 横跨层级的动作入口，不是 review 层级本身。
- `Task Panel`: 屏幕上的后台任务区域，不是 review 层级本身。
- `Browser Frame`: raw-key TTY 下的固定屏幕 frame，拥有 context/status、main content、task panel 和 prompt 四个渲染区域。

## Current Implementation Mapping

当前实现已经具备三层的大部分能力。内部页面命名现在通过 `BrowserPage` 表达产品语义，底层字符串值仍保持兼容旧 prompt、行模式和 `.git/cr/browse-state.json`：

```text
Review Scope
  current implementation:
    worktree/staged/all/base/range are commands
    Scope Home is BrowserPage.SCOPE_HOME -> "scopes"
    recent commits live in BrowserPage.COMMIT_PICKER -> "commits"
    selected commit is stored as selected_commit + ref_range

Changed Files
  current implementation:
    BrowserPage.CHANGED_FILES -> "list"
    visible_changes
    browse tree rows
    change source badges from FileChange.source
    source_filter
    seen_paths / remaining_only / review_notes

File Detail
  current implementation:
    BrowserPage.FILE_DETAIL -> "file"
    cached file lines
    file_scroll
    n/p navigation

Command Palette
  current implementation:
    BrowserPage.COMMAND_PALETTE -> "commands"
    command_filter_text

Task Panel / Browser Frame
  current implementation:
    cr.ui.tasks owns TaskState, TaskRecord history, command resolution, project task presets, process lifecycle, output capture, stop, rerun, foreground run, and history recording
    cr.ui.frame owns BrowserFrame, screen layout, Task Panel presentation, terminal line fitting, and Task Panel-only refresh output
    cr.ui.page_content owns page-specific main content rendering
    cr.ui.input owns terminal input protocol and raw-key reads
    browser.py owns prompt input interpretation and frame composition

Browser Navigation
  current implementation:
    BrowserNavigation owns page transitions, in-session page history, and local reset rules
    it does not load Git data, switch scopes, or render output

Review Workspace
  current implementation:
    ReviewWorkspace owns active scope, changed files, filter/progress/note state, selected file, selected commit, previous scope, and workspace-state data mapping

Browser Command Dispatch
  current implementation:
    BrowserCommandAction and parse_browser_command own command aliases, parameter parsing, numeric selections, and unknown fallback

Browser Action Execution
  current implementation:
    BrowserCommandExecutor owns parsed action execution and returns BrowserActionResult loop control
    cr.ui.selected_file_actions owns selected-file action workflows
    browser.py still owns prompt input interpretation, frame composition, and workspace startup/exit orchestration
```

Task Panel naming is now explicit without adding concurrent task management or moving browser code into a new module.
Page naming is now explicit without adding a true navigation stack or changing user-visible navigation behavior. `BrowserState.page` is the primary field; `BrowserState.mode` remains a compatibility property.
Navigation rules are now explicit. `BrowserNavigation` owns page transitions, local reset rules, and in-session back/forward page history for Changed Files, File Detail, Scope Home, Commit Picker, and Command Palette.
Review workspace rules are now explicit without changing Git review facts or persistence format. `ReviewWorkspace` owns scope switching, commit scope selection, filter/progress/note state, selected file state, and workspace-state data mapping.
Browser command dispatch is now explicit without changing user-visible commands. `BrowserCommandAction` and `parse_browser_command` map raw key aliases, line-mode commands, parameterized commands, and numeric selections to product actions before `browser.py` executes them.
Command catalog ownership is now explicit without changing user-visible commands. `cr.ui.command_catalog` owns grouped command help, executable palette entries, filtering/ranking, and command surface row rendering, while `browser.py` keeps command filter/selection/scroll state and frame placement.
Browser action execution is now explicit without changing user-visible behavior. `BrowserCommandExecutor` executes parsed actions and returns `BrowserActionResult`, while `run_browser` keeps prompt input, sentinels, workspace save-on-exit, and redraw scheduling.
Task runtime is now explicit without changing Task Panel behavior. `cr.ui.tasks` owns command resolution, process lifecycle, output capture, stop/rerun, foreground execution, and history records; `browser.py` keeps terminal layout and panel rendering.
Task presets are now explicit as project-local defaults. `cr.ui.tasks` reads `.cr/tasks.json` for build/test/lint defaults after CLI arguments and environment variables, and before DouyinHarmony's build fallback.
File actions are now explicit Changed Files operations. `open`, `copy path`, `copy anchor`, and `reveal` use browser command dispatch and action execution, while `cr.ui.file_actions` hides editor, clipboard, and file-browser subprocess details. `stage` and `unstage` are selected-file index actions: they mutate the local Git index through `cr.vcs.git` only for mutable local scopes, then refresh Changed Files.
File action configuration is now explicit. `--open-cmd` / `CR_OPEN_CMD`, `--copy-cmd` / `CR_COPY_CMD`, and `--reveal-cmd` / `CR_REVEAL_CMD` customize selected-file open/copy/reveal actions while preserving platform fallbacks.
File action diagnostics are now explicit. `file actions` shows open/copy/reveal command sources, and failures name the source that was attempted.
Task diagnostics are now explicit Task Runtime output. `tasks` shows build/test/lint command sources without starting a background process, and `cr.ui.tasks` owns malformed preset reporting.
Task preset schema help is now explicit Task Runtime output. `tasks help` shows `.cr/tasks.json` format, supported build/test/lint string commands, precedence, and a compact JSON example without starting a background process.
Change source badges are now explicit Changed Files metadata. `cr.vcs.git` annotates local changes as `staged`, `unstaged`, or `mixed`; `cr.ui.page_content` renders those badges in Changed Files rows. Base/range/commit scopes do not show mutable local index badges.
Change source filtering is now explicit Changed Files view state. `ReviewWorkspace` owns `source_filter`, `BrowserCommandAction` parses `source staged` / `source unstaged` / `source mixed` / `source all`, and `cr.ui.page_content` renders the active filter context.
Change source summary is now explicit Changed Files metadata. `cr.ui.page_content` derives visible `staged`, `unstaged`, and `mixed` counts from rendered `FileChange.source` facts and omits the summary for comparison scopes without local source facts.
Scope Home counts are now explicit first-layer overview metadata. `browser.py` samples Worktree, Staged, All local changes, and Recent commits counts when Scope Home opens or refreshes; `cr.ui.page_content` renders those counts on Scope Home rows; persistence does not store them.

## Implementation Rules

1. New review navigation features must identify which product layer they belong to: Review Scope, Changed Files, or File Detail.
2. A new mode is acceptable only if it maps to a product layer or a cross-layer overlay such as Command Palette.
3. Background task features belong to Task Panel and must not distort the review hierarchy.
4. Raw-key terminal writes must go through Browser Frame ownership rules.
5. Breadcrumb text should expose the product hierarchy, not internal mode names.
6. Scope switching should reset Changed Files and File Detail state unless explicitly designed otherwise.
7. File navigation should preserve the active Review Scope.
8. Workspace persistence should store product navigation state, not incidental rendering details.

## Near-Term Roadmap

### P0: Product navigation breadcrumbs

Status: implemented.

Render an explicit hierarchy line such as:

```text
Scope: worktree > Files
Scope: commit 71ee79d > Files > src/cr/ui/browser.py
```

This is the smallest change that makes the three product layers visible without rewriting state. Current implementation renders `Scope: <scope> > Files` for Changed Files, `Scope: <scope> > Files > <path>` for File Detail, and keeps `Scope: recent commits` as the commit picker / scope-selection surface.

### P0: Scope home

Status: implemented.

Promote Review Scope into a clearer first-level page. Current implementation exposes worktree, staged, all local changes, recent commits, and base/range command hints through `scopes` / `scope`. Base/range remain parameterized command entries (`: base REF`, `: range OLD..NEW`) rather than inline forms.

### P0: Page stack names

Status: implemented.

Wrap internal page values so implementation terms align with product terms:

```text
commits -> scope selection / commit picker
list -> changed files
file -> file detail
commands -> command palette
```

`BrowserPage` now names the existing pages as Scope Home, Commit Picker, Changed Files, File Detail, and Command Palette. The persisted string values remain unchanged, and `mode` stays as a compatibility property over `BrowserState.page`.

### P0: Task command breadth

Status: implemented.

`build`, `test` / `tests`, and `lint` now extend Task Panel instead of creating new product navigation layers. `stop` / `cancel` operate on the current task, and `rerun` / `rebuild` repeat the most recent task kind.

### P0: Navigation module deepening

Status: implemented.

`BrowserNavigation` now owns page transition intent and local reset rules. The browser main loop calls navigation actions rather than scattering raw `state.page = ...` assignments. This keeps current behavior stable while giving page-stack and ReviewWorkspace work a clearer place to attach.

### P0: ReviewWorkspace deepening

Status: implemented.

`ReviewWorkspace` now owns active Review Scope state, changed-file loading, filter/progress/note state, selected file state, selected commit, previous scope, and workspace-state data mapping. `cr.ui.page_content` owns page-specific main content rendering, while `browser.py` still owns prompt-input interpretation, selected-file action execution, and live state synchronization around persistence calls.

### P0: Workspace persistence extraction

Status: implemented.

`cr.ui.workspace_persistence` now owns `.git/cr/browse-state.json` path construction, schema version wrapping and validation, tolerant JSON read/write, and default-session restore/save eligibility. `ReviewWorkspace` keeps product state interpretation, and `browser.py` keeps startup/exit orchestration plus live `BrowserState` synchronization.

### P0: Browser Frame extraction

Status: implemented.

`cr.ui.frame` now owns Browser Frame screen-layer behavior: terminal height and line fitting, content/task/prompt region layout, Task Panel line presentation, and Task Panel-only partial refresh output. `browser.py` keeps prompt-input interpretation, command execution, frame composition, and workspace startup/exit orchestration.

### P0: Page Content extraction

Status: implemented.

`cr.ui.page_content` now owns browser page main-content rendering: prompt labels, help lines, scope breadcrumbs/context, Scope Home entries, Changed Files tree rows, Commit Picker rows, empty states, File Detail lines, and scroll-window calculations. `browser.py` keeps compatibility wrappers plus prompt-input interpretation, Browser Frame composition, command execution, selected-file side effects, and workspace startup/exit orchestration.

### P0: Browser Input extraction

Status: implemented.

`cr.ui.input` now owns browser terminal input protocol: raw-key availability checks, browse command reads, temporary filter/command query reads, raw escape-sequence mapping, idle tick, EOF, and interrupt sentinels. `browser.py` keeps compatibility wrappers plus prompt-input interpretation, frame dirty/redraw recovery, workspace save-on-exit, command execution, selected-file side effects, and workspace startup/exit orchestration.

### P0: Selected File Actions extraction

Status: implemented.

`cr.ui.selected_file_actions` now owns selected-file workflows: open selected file, copy selected path, copy selected anchor, reveal selected file, set/clear selected-file note, prompt handoff selection, and copy/save prompt handoff messages. `BrowserCommandExecutor` keeps parsed action routing and Browser Frame status placement, while `cr.ui.file_actions`, `cr.ui.handoff`, and `cr.review.prompt` keep platform/process, file-write, and Markdown rendering responsibilities.

### P0: Command dispatch deepening

Status: implemented.

`BrowserCommandAction` and `parse_browser_command` now own the browser command language. The main browser loop parses command text once into product actions, then executes those actions with the existing behavior. This keeps command aliases, parameter extraction, numeric selections, raw-key slash handling, and unknown-command fallback in one place.

### P0: Command action execution deepening

Status: implemented.

`BrowserCommandExecutor` now owns parsed action execution for browser commands. The run loop resolves temporary prompts and palette handoff, parses the final command, then asks the executor for `BrowserActionResult` so exit intent and redraw requests are explicit.

### P0: Command palette organization

Status: implemented.

Command palette filtering now shows match counts and ranks stronger command/label matches ahead of group and description-only matches. Unfiltered palette order remains the stable catalog order.

### P0: Command catalog extraction

Status: implemented.

`cr.ui.command_catalog` now owns command catalog groups, executable command palette entries, command filtering/ranking, command list lines, and command palette screen lines. `browser.py` keeps mutable command palette state such as filter text, selection, scroll position, and frame placement, but no longer owns catalog data or ranking rules.

### P0: Task runtime extraction

Status: implemented.

`cr.ui.tasks` now owns Task Panel runtime behavior: build/test/lint command resolution, process lifecycle, output drain, stop escalation, rerun, foreground execution, and compact task history. `cr.ui.frame` owns the bottom panel's screen presentation and frame layout.

### P0: Task configuration presets

Status: implemented.

`cr.ui.tasks` now reads project-local `.cr/tasks.json` defaults for build/test/lint. CLI arguments and environment variables remain higher-priority temporary overrides, while DouyinHarmony's default build remains the final build fallback.

### P0: File action breadth

Status: implemented.

`open`, `copy path`, `copy anchor`, and `reveal` now operate on the selected changed file through the browser command parser, command palette, and action executor. `open` remains the editor handoff to the first changed line.

### P0: File action configuration

Status: implemented.

`--open-cmd` / `CR_OPEN_CMD`, `--copy-cmd` / `CR_COPY_CMD`, and `--reveal-cmd` / `CR_REVEAL_CMD` customize selected-file actions. `cr.ui.file_actions` owns template expansion, environment lookup, platform fallback, and subprocess behavior for open/copy/reveal.

### P0: Editor handoff diagnostics

Status: implemented.

`file actions` now shows open/copy/reveal source resolution without executing actions. File action failures include CLI/env/platform/missing source context, so users can see whether a failed handoff came from explicit config, environment, platform fallback, or absent tooling.

### P0: Task preset diagnostics

Status: implemented.

`tasks` now shows build/test/lint command sources through the command parser, command palette, and action executor. `cr.ui.tasks` owns the resolution explanation and reports malformed `.cr/tasks.json` without changing tolerant task execution.

### P0: Task preset schema help

Status: implemented.

`tasks help` now shows the expected `.cr/tasks.json` shape, supported build/test/lint string commands, task command precedence, and a compact JSON example. Malformed preset diagnostics point to this help without making preset parsing fatal.

### P0: Review notes

Status: implemented.

`note TEXT` now sets a lightweight per-file note for the selected changed file, and `note` clears it. Changed Files shows a compact note marker, File Detail shows the full note text, and `.git/cr/browse-state.json` persists notes with the default review workspace.

`notes` summarizes the current workspace's review notes without changing the active page, selection, scope, or task state. Notes for files in the active changed-file list follow review order; persisted notes outside the active changes are still shown after that, sorted by path.

`notes QUERY` filters that summary by path or note text with case-insensitive substring matching. The filter is command-local and does not change file filters, page state, selection, scope, or task state.

`copy notes` / `notes copy` copies the full summary through the existing copy action configuration, while `copy notes QUERY` copies the same filtered summary that `notes QUERY` would show. Empty note sets or empty filtered matches report an empty state without launching a clipboard command.

### P0: Browser prompt handoff

Status: implemented.

`copy prompt` copies prompt-ready Markdown for the current visible changed files through the existing copy action configuration. `save prompt [PATH]` writes the same Markdown to a file, defaulting to `.cr/handoff/review-prompt.md`.

`copy prompt file` copies prompt-ready Markdown for only the selected visible changed file, including that file's review note when present. `save prompt file [PATH]` writes the same selected-file Markdown to a file, defaulting to `.cr/handoff/review-prompt-file.md`. All four commands preserve the active page, selection, Review Scope, file filter, progress markers, review notes, and task state. Empty visible scopes report an empty state without launching a clipboard command or writing a file.

### P0: Real page stack

Status: implemented.

`BrowserNavigation` now keeps an in-session page back/forward stack. `back` restores the previous page snapshot, `forward` restores the page left by `back`, new navigation branches clear forward history, and Review Scope switches / refreshes reset the stack.

### P0: Selected-file index actions

Status: implemented.

`stage` and `unstage` now operate on the selected changed file from Changed Files or File Detail. They use the browser command parser, command palette, `BrowserCommandExecutor`, `cr.ui.selected_file_actions`, and `cr.vcs.git`. Successful actions refresh the active mutable local Review Scope and return to Changed Files; base/range/commit scopes stay read-only.

### P0: Change source badges

Status: implemented.

Changed Files rows now show local change source badges. `staged` means the path currently has index changes, `unstaged` means worktree-only changes, and `mixed` means both sides have changes for the same path. These badges are facts from `cr.vcs.git.FileChange.source`, rendered by `cr.ui.page_content`; comparison scopes stay badge-free.

### P0: Change source filter

Status: implemented.

Changed Files now supports `source staged`, `source unstaged`, `source mixed`, and `source all`. This filter lives in `ReviewWorkspace`, composes with path filtering and remaining-only mode, shows active filter context in Changed Files, and resets on Review Scope switches.

### P0: Change source summary

Status: implemented.

Changed Files now shows a compact source summary for the currently visible list, such as `Sources: staged 2, unstaged 5, mixed 1`. The summary is derived by `cr.ui.page_content` from rendered `FileChange.source` facts, omits zero-count sources, and stays hidden for comparison scopes that do not have local index/worktree source facts.

### P0: Scope Home counts

Status: implemented.

Scope Home now shows live overview counts beside directly countable first-layer entries: Worktree, Staged, All local changes, and Recent commits. Counts are sampled by `browser.py` when Scope Home opens or refreshes, respect existing path/code/untracked filters for changed-file scopes, and stay out of workspace persistence.

## Architecture Check Cadence

Use the architecture skill periodically, especially before changes that touch `src/cr/ui/browser.py`, `src/cr/review/changes.py`, or workspace persistence.

Keep the product navigation terms language-neutral. `Review Scope`, `Changed Files`, `File Detail`, `Command Palette`, `Task Panel`, and `Browser Frame` should remain stable even if the implementation later moves away from Python. Internal Python strings such as `mode="list"` or `mode="file"` are implementation details, not long-term product interfaces.

Current architecture risk:

- `src/cr/ui/browser.py` is still a large module that owns session orchestration, prompt-input interpretation, action routing, frame composition, and workspace startup/exit.
- `BrowserNavigation` hides page transition rules, `ReviewWorkspace` hides active review workspace rules and path/source filtering, `Workspace Persistence` hides persisted workspace file I/O, `Browser Frame` hides screen-layer layout and Task Panel presentation, `Browser Input` hides terminal input protocol, `Page Content` hides product-page main content rendering plus Scope Home count display and source-badge/filter-context/summary display, `Selected File Actions` hides current-file workflows and local index-action gating, `BrowserCommandAction` hides command string parsing, `Command Catalog` hides command surface data/filtering/rendering, `BrowserCommandExecutor` hides action execution, `cr.ui.tasks` hides task runtime behavior, `cr.ui.file_actions` hides open/copy/reveal platform behavior, and `cr.vcs.git` hides Git index subprocess behavior plus local change source facts.
- The next product opportunity should come from concrete usage friction around richer review handoff workflows or broader IDE-like file operations.
