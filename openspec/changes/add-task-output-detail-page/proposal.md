## Why

`cr browse` 已经有后台 Task Panel，也能 `copy task` / `save task` handoff 当前任务输出，但长日志仍只能在底部 5-10 行里滚动经过。用户在编译时希望继续看代码，同时需要一个可进入、可滚动的日志详情页，用来检查完整输出和保留上下文。

## What Changes

- 增加 `Task Output` browser page，显示当前任务的类型、状态、命令和已捕获输出。
- 增加 `task output` / `output` 命令，从任意页面进入该页，并进入 page history。
- 在 Task Output 页支持 ↑/↓、PgUp/PgDn、Home/End 滚动输出，`b` 返回上一页。
- Task Output 页的 contextual action bar 展示 `copy task`、`save task`、`stop`、`rerun` 等相关动作。
- 任务运行时，普通页面仍只局部刷新底部 Task Panel；只有用户停在 Task Output 页时才刷新主内容以呈现最新日志。
- 不新增历史任务浏览、不解析错误诊断、不改变 task lifecycle 或输出捕获容量。

## Capabilities

### New Capabilities
- `task-output-detail-page`: 在 workbench 内打开并滚动查看当前任务输出。

### Modified Capabilities
- `browser-page-navigation`: 导航栈支持 Task Output 页。
- `task-output-handoff`: Task Output 页暴露复制/保存当前任务输出的高频动作。

## Impact

- 影响 `cr.ui.navigation` 的页面枚举和导航转换。
- 影响 `cr.ui.commands`、`cr.ui.command_catalog` 的命令路由与命令列表。
- 影响 `cr.ui.page_content` 的 prompt、breadcrumb、action bar 和 task output screen lines。
- 影响 `cr.ui.browser` 的绘制分支、滚动状态和任务 tick 刷新策略。
- 不改变 CLI 参数、不新增依赖、不改变 `.cr/tasks.json` 或 workspace persistence schema。
