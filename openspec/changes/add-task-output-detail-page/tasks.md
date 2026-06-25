## 1. 行为测试

- [x] 1.1 增加 page model/navigation 测试，覆盖 `BrowserPage.TASK_OUTPUT`、导航栈和返回行为。
- [x] 1.2 增加 command parser/catalog 测试，覆盖 `task output` / `output` 入口。
- [x] 1.3 增加 page content 测试，覆盖 Task Output prompt、breadcrumb、action bar、空状态和输出渲染。
- [x] 1.4 增加 BrowserCommandExecutor / draw 测试，覆盖进入页面、滚动、Home/End 和 task tick 刷新策略。

## 2. 实现

- [x] 2.1 在 `cr.ui.navigation` 增加 Task Output 页、快照字段和 `show_task_output`。
- [x] 2.2 在 `cr.ui.commands` / `cr.ui.command_catalog` 增加 Task Output 命令入口。
- [x] 2.3 在 `cr.ui.page_content` 增加 Task Output prompt、breadcrumb、action bar 和 screen lines。
- [x] 2.4 在 `cr.ui.browser` 增加 `task_scroll`、绘制分支、滚动逻辑和 tick 刷新策略。

## 3. 文档与验证

- [x] 3.1 更新 README、CONTEXT、设计文档、P0 记录和导航文档。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查改动范围，确认没有引入历史任务浏览、诊断解析或 task lifecycle 变化。
