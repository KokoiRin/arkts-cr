## Context

`BrowserNavigation` 已经收拢了页面跳转规则，但 `browser.py` 仍直接拥有 review workspace 的多步协议：

- 从 `argparse.Namespace` 读取当前 scope。
- 用 `selected_changes(args)` 和 `sort_changes(..., args.sort)` 加载 changed files。
- 选择 commit 时捕获 previous scope，并把 args 改成 commit ref range。
- 切换 worktree/staged/all/base/range 时重置 selected commit、filter、render cache、scroll 和 selection。
- 恢复 workspace state 时读取 scope/filter/selection/progress 并回填到 `BrowserState`。

这些规则都是 in-process + local Git adapter 之上的同步逻辑。第一阶段不需要新 port；测试可以通过注入 loader 函数来验证 workspace 行为。

## Goals / Non-Goals

**Goals:**

- 新增 `ReviewWorkspace` module，拥有 active scope、changed files、selected commit、previous scope、filter/progress 和 selected index。
- 提供小 interface：load default workspace、switch scope、select commit、restore previous scope、visible changes、restore/save data assembly。
- 让 `browser.py` 通过 workspace 行为完成 scope 切换，而不是直接拼接 args + state 字段。
- 保持现有用户行为、prompt、持久化 JSON 和测试语义不变。
- 让 scope/commit/restore 规则可以直接通过 workspace interface 测试。

**Non-Goals:**

- 不改变 `cr.review.changes` 的 Git fact 生成逻辑。
- 不改变 workspace state 文件路径、版本号或 JSON 字段。
- 不把 Task Panel、Browser Frame、Command Palette 或 raw-key 输入迁入 workspace。
- 不实现真实 page stack。
- 不一次性拆空 `browser.py`。

## Decisions

### Decision 1: `ReviewWorkspace` owns review state, `BrowserState` stays as UI shell

第一阶段让 `BrowserState` 继续存在，并逐步委托给 `ReviewWorkspace`。这样渲染和现有测试可以稳定过渡，避免一次性迁移所有调用方。

替代方案是直接把 `BrowserState.changes/filter/selected/...` 全部删除。暂不采用，因为这会把渲染、命令分发和 workspace 迁移绑成大重构。

### Decision 2: Scope loader is injectable, not a public port

`ReviewWorkspace` 可以接收 loader callable，默认仍使用现有 `selected_changes + sort_changes`。测试中注入 fake loader 即可；这属于 internal seam，不引入长期 public port。

### Decision 3: Persistence format remains browser-owned for now

本轮可把 data assembly/restore behavior 向 workspace 靠拢，但不改变 `_browser_workspace_state_path`、版本号、读写容错和外部 JSON。文件 I/O 留在 browser 边缘，workspace 只负责解释/生成数据。

### Decision 4: Keep args mutation contained but compatible

现阶段 CLI args 仍是 Git scope adapter 的输入。`ReviewWorkspace` 可以读写 args 以保持兼容，但它应集中这些 writes，后续再把 args 替换为更明确的 scope config。

## Risks / Trade-offs

- `ReviewWorkspace` 可能和 `BrowserState` 短期重叠 → 缓解：第一阶段只迁移 scope/changes/filter/selection/progress，任务和渲染状态不进 workspace。
- 注入 loader 可能看起来像过早 port → 缓解：只作为构造参数/internal seam，用于测试和默认实现，不向 CLI 暴露。
- 持久化未完全迁出 browser → 缓解：本轮目标是 review workspace 规则集中，文件 I/O 边缘化留到后续。
