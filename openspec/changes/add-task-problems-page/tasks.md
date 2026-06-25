## 1. 行为测试

- [x] 1.1 增加 `cr.ui.task_problems` 单元测试，覆盖相对路径、repo 内绝对路径、列号、去除 ANSI、忽略不存在文件/URL。
- [x] 1.2 增加 command parser/catalog 测试，覆盖 `problems` / `task problems`。
- [x] 1.3 增加 page model/navigation/content 测试，覆盖 Task Problems 页、空状态、列表展示和 action bar。
- [x] 1.4 增加 BrowserCommandExecutor 测试，覆盖打开页面、选择滚动、Enter 打开选中问题、无 task/无问题空状态。

## 2. 实现

- [x] 2.1 新增 `cr.ui.task_problems` 纯解析模块。
- [x] 2.2 在 navigation/state 中增加 Task Problems 页、选择和滚动状态。
- [x] 2.3 在 commands/catalog/page_content 中增加命令入口和页面渲染。
- [x] 2.4 在 browser executor 中增加打开页、选择滚动和 Enter 打开问题。

## 3. 文档与验证

- [x] 3.1 更新 README、CONTEXT、设计文档、P0 记录和导航文档。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查改动范围，确认没有引入专有 diagnostics parser、历史任务搜索或 task lifecycle 变化。
