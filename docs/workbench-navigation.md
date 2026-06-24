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

### 2. Changed Files

Changed Files 是二级对象：它展示当前 Review Scope 里改动了哪些文件。

这层负责：

- 文件树和路径层级。
- 每个文件的 added/deleted 统计。
- 文件状态：modified、added、deleted、renamed、untracked。
- 轻量 review 进度：seen/todo、remaining。
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
- 打开外部编辑器。
- 在当前 scope 的文件之间 next/previous。

这层必须始终知道自己属于哪个 Review Scope 和哪个 Changed Files 集合。`back` 应返回 Changed Files；再次返回才回到上一层 scope 选择或默认工作区入口。

## Persistent Navigation Terms

后续代码、文档和测试优先使用这些词：

- `Review Scope`: 当前 review 的变化集合。
- `Changed Files`: 某个 scope 下的文件树/文件列表层。
- `File Detail`: 某个文件的具体 diff/outline/detail 层。
- `Command Palette`: 横跨层级的动作入口，不是 review 层级本身。
- `Task Panel`: 屏幕上的后台任务区域，不是 review 层级本身。
- `Browser Frame`: raw-key TTY 下的固定屏幕 frame，拥有 context/status、main content、task panel 和 prompt 四个渲染区域。

## Current Implementation Mapping

当前实现已经具备三层的大部分能力，但命名和入口还不够清晰：

```text
Review Scope
  current implementation:
    worktree/staged/all/base/range are commands
    recent commits live in mode="commits"
    selected commit is stored as selected_commit + ref_range

Changed Files
  current implementation:
    mode="list"
    visible_changes
    browse tree rows
    seen_paths / remaining_only

File Detail
  current implementation:
    mode="file"
    cached file lines
    file_scroll
    n/p navigation

Command Palette
  current implementation:
    mode="commands"
    command_filter_text

Task Panel / Browser Frame
  current implementation:
    BuildState
    TaskRecord history
    BrowserFrame
```

The next implementation work should make this mapping more explicit without doing a risky rewrite in one step.

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

### P1: Page stack names

Rename or wrap internal `mode` values so implementation terms align with product terms:

```text
commits -> scope selection / commit picker
list -> changed files
file -> file detail
commands -> command palette
```

This should be done behind tests and without breaking line-mode compatibility.

### P0: Task command breadth

Status: implemented.

`build`, `test` / `tests`, and `lint` now extend Task Panel instead of creating new product navigation layers. `stop` / `cancel` operate on the current task, and `rerun` / `rebuild` repeat the most recent task kind.

## Architecture Check Cadence

Use the architecture skill periodically, especially before changes that touch `src/cr/ui/browser.py`, `src/cr/review/changes.py`, or workspace persistence.

Keep the product navigation terms language-neutral. `Review Scope`, `Changed Files`, `File Detail`, `Command Palette`, `Task Panel`, and `Browser Frame` should remain stable even if the implementation later moves away from Python. Internal Python strings such as `mode="list"` or `mode="file"` are implementation details, not long-term product interfaces.

Current architecture risk:

- `src/cr/ui/browser.py` is becoming a large module that owns session state, navigation, rendering, command handling, build lifecycle, and editor handoff.
- The next deepening opportunity is likely task-state naming (`BuildState` / `_poll_build` / `_record_completed_build`) because Task Panel now covers build/test/lint while some internals still carry build-specific names.
- After that, consider a `BrowserNavigation` or `ReviewWorkspace` module whose interface hides scope/list/file transitions from the render loop.
