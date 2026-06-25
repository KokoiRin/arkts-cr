## 1. 行为测试

- [x] 1.1 增加 Task Runtime 单元测试，覆盖 running/completed/empty-output 的 task output handoff 文本。
- [x] 1.2 增加 command parser/catalog 测试，覆盖 `copy task`、`save task` 和 `save task PATH`。
- [x] 1.3 增加 BrowserCommandExecutor 测试，覆盖复制、保存、自定义路径和无 task 空状态。

## 2. 实现

- [x] 2.1 在 `cr.ui.tasks` 中实现当前 task output Markdown 生成。
- [x] 2.2 在 `cr.ui.handoff` 中增加 task output 默认路径和保存 helper。
- [x] 2.3 增加 task output handoff command actions，并接入 executor、command catalog 和 contextual action bar。

## 3. 文档与验证

- [x] 3.1 更新 README、设计文档、P0 记录和架构上下文，说明 task output handoff 的用法和模块归属。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查改动范围，确认没有引入诊断解析、历史持久化或 task lifecycle 变更。
