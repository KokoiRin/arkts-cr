## 1. 行为测试

- [x] 1.1 增加 source file model/text-search 测试，覆盖搜索命中行和缺失查询。
- [x] 1.2 增加 BrowserCommandExecutor 测试，覆盖 Source File Page `find TEXT`、`next match`、`prev match`。
- [x] 1.3 增加空/不可读 source 的 find 测试，确认报错且不崩溃。
- [x] 1.4 增加 action bar/parser/page model 测试，确认 Source File Page 暴露 find/next match。

## 2. 实现

- [x] 2.1 在 source-file/page 状态中增加 `source_find_text`。
- [x] 2.2 在 browser find dispatch 中接入 Source File Page。
- [x] 2.3 复用 `text_search` 实现 source find 和 repeated match wraparound。
- [x] 2.4 更新 Source File Page action bar。

## 3. 文档与验证

- [x] 3.1 更新 README、CONTEXT、设计文档、P0 记录和导航文档。
- [x] 3.2 运行 OpenSpec strict validation、聚焦测试、`git diff --check`、`compileall` 和全量 unittest。
- [x] 3.3 用 Warden 审查范围，确认没有引入编辑、syntax parser、cross-file search、persistence、diagnostics parser 或 task lifecycle 变化。
