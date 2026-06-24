## Why

`cr browse` 正在朝 terminal workbench 演进，但 `src/cr/ui/browser.py` 仍直接协调 review scope、changed-file loading、commit scope selection、previous scope 和 workspace restore。继续往 IDE 替代方向扩展时，这会让“当前 review 工作区是什么”这件事散落在 UI 主循环里。

本轮做一小步架构加深：新增 `ReviewWorkspace` module，让 active Review Scope 和 changed files 的加载/重置规则集中到一个 in-process module 中。

## What Changes

- 新增 `ReviewWorkspace` module，集中表达当前 review scope、changed files、selected commit、previous scope 和 filter/progress 状态。
- 将 worktree/staged/all/base/range scope 切换、commit scope 选择、previous scope restore 的核心规则迁入该 module。
- 保留 `BrowserState` 作为 UI/session state 的兼容壳，不改变现有 render、key handling、Task Panel 或 command palette。
- 保持 `.git/cr/browse-state.json` 的外部字段和值不变。
- 不新增用户命令，不改变 Git diff 行为，不实现真实 page stack。

## Capabilities

### New Capabilities

- `review-workspace-module`: 浏览器的 active Review Scope 和 changed-file workspace 由一个 module 拥有，UI 调用方通过 workspace 行为切换 scope 和加载 changes。

### Modified Capabilities

无。

## Impact

- 主要影响 `src/cr/ui/browser.py`。
- 可能新增 `src/cr/ui/workspace.py`，作为 `cr.ui` 内部 module。
- 需要更新导航/工作区相关测试、`CONTEXT.md`、`docs/design.md`、`docs/workbench-navigation.md` 和 `docs/p0.md`。
- 不新增运行时依赖，不改变 CLI 参数或持久化文件格式。
