## 1. 行为测试

- [x] 1.1 增加 `cr.ui.task_problems` handoff 文本测试，覆盖单个 problem 和 all problems。
- [x] 1.2 增加 command parser/catalog 测试，覆盖 `copy problem` / `copy problems`。
- [x] 1.3 增加 Task Problems action bar 测试，暴露复制入口。
- [x] 1.4 增加 BrowserCommandExecutor 测试，覆盖复制选中 problem、复制所有 problems、空 problems 不调用 clipboard。

## 2. 实现

- [x] 2.1 在 `cr.ui.task_problems` 中增加 location/handoff text helper。
- [x] 2.2 在 command dispatch/catalog/page content 中增加复制命令和当前页 action。
- [x] 2.3 在 BrowserCommandExecutor 中接入 copy problem/copy problems。

## 3. 文档与验证

- [x] 3.1 更新 README、CONTEXT、设计文档、P0 记录和导航文档。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查范围，确认没有引入专有 diagnostics parser、历史任务搜索、persistence 或 task lifecycle 变化。
