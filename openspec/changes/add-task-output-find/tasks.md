## 1. 行为测试

- [x] 1.1 增加 `cr.ui.text_search` 单元测试，覆盖大小写不敏感、ANSI 清理、首行跳过和循环跳转。
- [x] 1.2 增加 File Detail find 回归测试或保持现有测试通过，确认抽取不改变行为。
- [x] 1.3 增加 BrowserCommandExecutor 测试，覆盖 Task Output `find TEXT`、`next match`、`prev match`、空 query、无 task 和无匹配。
- [x] 1.4 增加 Task Output action bar / 文档测试覆盖 `find` 提示。

## 2. 实现

- [x] 2.1 新增 `cr.ui.text_search` 纯 helper。
- [x] 2.2 调整 `file_detail_navigation` 复用 `text_search`，保持返回类型和消息不变。
- [x] 2.3 在 `BrowserState` 增加 `task_find_text`，并在 find action 中按页面分发 File Detail / Task Output。
- [x] 2.4 在 `page_content` Task Output action bar 中加入 find 相关提示。

## 3. 文档与验证

- [x] 3.1 更新 README、CONTEXT、设计文档、P0 记录和导航文档。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查改动范围，确认没有引入 diagnostics、历史任务搜索或 task lifecycle 变化。
