## Context

`cr browse` 的底层数据层已经支持多个 review scope：默认 worktree、`--staged`、`--all`、`--base REF`、`--range OLD..NEW`，以及通过 recent commits 进入单个 commit diff。当前问题不是 Git 能力不足，而是 TUI 页面没有把这些 scope 作为一等工作区展示出来。结果是用户切到 commit 或从 staged 启动后，页面仍然主要显示 “Changed files”，缺少“我现在看的是哪一层”的感知。

## Goals / Non-Goals

**Goals:**

- 在 list、file、commit list 等主视图中显示当前 review scope。
- 支持会话内切换 `worktree`、`staged`、`all`、`base REF`、`range OLD..NEW`。
- 选中 recent commit 后显示 commit scope；回到 commit list 时显示 recent commits scope。
- 切换 scope 后清空 filter、render cache、selection 和 scroll，防止旧 scope 状态污染新 scope。
- 保持 build 面板、文件导航、过滤和 recent commits 现有行为。

**Non-Goals:**

- 不实现完整 command palette、命令补全或命令帮助弹窗。
- 不改变 Git 数据层、diff 语义或 CLI 参数语义。
- 不增加 persistent workspace/session 状态。
- 不把 browser scope 抽成跨 package 公共 API；当前只服务 interactive browser。

## Decisions

### Decision: argparse namespace 继续作为 scope 权威源

现有 `selected_changes(args)`、hunk 渲染、first changed line、outline 都已经从 `args.staged`、`args.all_changes`、`args.base`、`args.ref_range`、`args.untracked` 读取 scope。本轮只新增局部 helper 更新这些字段并重载 browser state。

备选方案是新建 `ReviewWorkspace` model。它更整洁，但会形成第二份 scope 数据源，反而容易和现有 review pipeline 脱节。

### Decision: scope header 是页面上下文层的一部分

在帮助/上下文区下方展示 `Scope: ...`，而不是塞进每个文件行或 prompt。这样 list、file、commit list 都能共享同一条上下文，不占用文件树的层级视觉。

备选方案是把 scope 放在 prompt，例如 `cr:worktree:list>`。这会让 prompt 变长，且 file/list/commit 三种 mode 已经占用 prompt 语义。

### Decision: scope switching 只在 command 层处理

支持 `worktree`、`staged`、`all`、`base REF`、`range OLD..NEW` 这些文本命令。raw-key 快捷键暂不增加，避免和现有 `u/d/w/g` 导航键继续冲突。

备选方案是为 staged/all/base 增加单键快捷键。它操作快，但现在更缺的是清晰层级而不是更多快捷键；等 command palette 成形后再决定快捷键。

## Risks / Trade-offs

- [Risk] `w` 过去在 commit review 中表示回到原 scope；新增 `worktree` 显式切换可能让语义更复杂。→ Mitigation：保留 `w` 的“回到进入 commit 前的 scope”行为，新增完整命令 `worktree` 用于显式切换默认 worktree。
- [Risk] `base REF` 和 `range OLD..NEW` 输入错误会直接走 Git 并抛错。→ Mitigation：本轮使用现有 GitError 顶层处理；后续 command palette 可做更好的 inline error。
- [Risk] scope header 占一行，会减少小终端可见内容。→ Mitigation：这是上下文层核心信息，优先级高于多显示一行文件树。
