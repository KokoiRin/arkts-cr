## 1. 行为测试

- [x] 1.1 增加 Page Content 动作条单元测试，覆盖 Changed Files、File Detail、Scope Home、Commit Picker、Command Palette。
- [x] 1.2 增加 Browser Frame 渲染测试，确认动作条出现在 raw-key full redraw 中并与 Task Panel 共存。
- [x] 1.3 增加回归测试，确认动作条不进入 workspace persistence state 且既有命令解析行为不变。

## 2. 实现

- [x] 2.1 在 `cr.ui.page_content` 中实现页面相关 contextual action bar 文案。
- [x] 2.2 在 raw-key `_draw_browse_screen` 中把动作条组合到 scope/status line 之后、页面主体之前。
- [x] 2.3 确保动作条使用终端单行截断，并且不会改变非 raw-key line-mode 输出。

## 3. 文档与验证

- [x] 3.1 更新 README、设计文档和 P0 记录，说明动作条的用户价值和模块归属。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查改动范围，确认没有新增命令语义、状态 schema 或过度抽象。
