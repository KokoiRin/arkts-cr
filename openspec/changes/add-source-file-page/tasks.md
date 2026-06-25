## 1. 行为测试

- [x] 1.1 增加 `cr.ui.source_file` 测试，覆盖 repo 内文件读取、line clamp、windowing、缺失/非 UTF-8 文件错误。
- [x] 1.2 增加 page model/navigation/parser/catalog/action bar 测试，覆盖 Source File Page 和 `view problem`。
- [x] 1.3 增加 page content 测试，覆盖源文件行号、target line marker、empty/error state。
- [x] 1.4 增加 BrowserCommandExecutor 测试，覆盖 Task Problems 中 `view problem` 打开 Source File Page、滚动、空 problems 状态。

## 2. 实现

- [x] 2.1 新增 `cr.ui.source_file` read-only source view model。
- [x] 2.2 在 navigation/state 中增加 Source File Page 和状态字段。
- [x] 2.3 在 commands/catalog/page_content 中增加命令入口和页面渲染。
- [x] 2.4 在 browser executor/draw loop 中接入 view problem 和 source scrolling。

## 3. 文档与验证

- [x] 3.1 更新 README、CONTEXT、设计文档、P0 记录和导航文档。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查范围，确认没有引入编辑、syntax parser、diagnostics parser、history search、persistence 或 task lifecycle 变化。
