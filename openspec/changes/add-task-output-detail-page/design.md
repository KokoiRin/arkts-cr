## Context

当前 workbench 的主层级是：

1. Review Scope：工作区、暂存区、全部本地改动、base/range、recent commit。
2. Changed Files：当前 scope 下的文件树和文件级 review 进度。
3. File Detail：单个文件的 diff、符号、风险、行级动作。

Task Panel 是横跨这些层级的运行状态区，适合给出 5-10 行最新输出；它不是完整日志阅读界面。`copy task` / `save task` 已经解决“把日志交出去”的问题，但还缺“在 TUI 内读日志”的页面。

## Goals / Non-Goals

**Goals:**

- 让用户可以通过 `task output` 或 `output` 进入当前任务输出详情页。
- 详情页显示任务标签、状态、命令和当前捕获输出。
- 详情页使用独立 `task_scroll`，支持行滚动、翻页、首尾跳转。
- 导航栈保留来源页面，`b` 能回到用户刚才看代码的位置。
- 运行中 task 在普通页面继续只刷新底部 panel；在 Task Output 页刷新主内容。

**Non-Goals:**

- 不浏览历史任务输出。
- 不持久化 task output 或 `task_scroll`。
- 不解析错误、warning、文件位置或新增 Problems 页。
- 不改变 task output capture 容量。
- 不改变 build/test/lint 启停策略。

## Decisions

1. **Task Output 是 BrowserPage，而不是 Task Panel 展开态。**
   - 选择：新增 `BrowserPage.TASK_OUTPUT = "task-output"`。
   - 理由：它有独立 prompt、breadcrumb、action bar、滚动状态和导航历史，行为更像 IDE Output 面板。

2. **输出页面复用 TaskState 快照。**
   - 选择：页面渲染读取当前 `state.task`，没有 task 时显示空状态。
   - 理由：当前 `TaskRecord` 不保留完整输出，从历史补日志会误导用户。

3. **滚动状态放在 BrowserState。**
   - 选择：新增 `task_scroll`，页面切换到 Task Output 时重置为 0，滚动命令只改变该字段。
   - 理由：与 `file_scroll`、`commit_scroll`、`command_scroll` 的已有模式一致。

4. **Task Output 页运行时整屏刷新，其他页面仍局部刷新 panel。**
   - 选择：处理 idle tick 时，如果当前页是 Task Output，则安排完整 redraw；否则调用现有 `_draw_task_panel_only`。
   - 理由：日志详情页需要看到新输出；普通代码阅读页优先稳定不闪。

## Risks / Trade-offs

- **长输出仍有限**：页面展示的是 TaskState 当前捕获的行，不扩大捕获容量，避免内存和行为范围变化。
- **整屏刷新可能轻微闪动**：只在用户主动进入 Task Output 页时发生，普通页面保持局部刷新。
- **空状态可能让用户误以为历史没了**：页面文案明确只显示 current task output，引导使用 build/test/lint 先启动任务。
