## Why

Task Output Page 已经能展开长日志，但用户遇到编译失败或测试失败时仍需要靠肉眼翻页找关键词。IDE 的 Output Panel 通常支持搜索当前输出；`cr browse` 要替代 IDE 的高频工作流，也需要在任务日志详情页里快速定位文本。

## What Changes

- 在 Task Output Page 支持 `find TEXT`，搜索当前任务已捕获输出并跳到首个匹配行。
- 在 Task Output Page 支持 `next match` / `prev match`，复用最近一次非空 task output find query 并循环跳转。
- 查找大小写不敏感，并忽略 ANSI 样式码。
- Task Output Page action bar 提示 `find` / `next match`。
- 抽出 UI rendered-text search 小模块，让 File Detail 和 Task Output 共用纯文本查找核心，避免 Task Output 依赖 File Detail navigation。
- 不解析 diagnostics、不打开文件、不搜索历史任务、不改变 task output 捕获容量。

## Capabilities

### New Capabilities
- `task-output-find`: 在当前任务输出详情页内搜索和重复跳转文本匹配。

### Modified Capabilities
- `file-detail-find`: File Detail 查找继续保持现有行为，但底层复用通用 rendered-text search helper。

## Impact

- 影响 `cr.ui.browser` 的 find action 分发和 Task Output 状态。
- 影响 `cr.ui.page_content` 的 Task Output action bar 文案。
- 新增 `cr.ui.text_search` 纯 helper 模块。
- 小幅调整 `cr.ui.file_detail_navigation`，把通用 find 逻辑委托给 `cr.ui.text_search`。
- 不改变 CLI 参数、workspace persistence、task runtime 或 task lifecycle。
