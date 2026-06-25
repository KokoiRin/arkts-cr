## Why

Task Output Page 已经能展开、搜索 build/test/lint 日志，但 IDE 的高频闭环还缺一步：从错误日志里的文件位置直接跳到代码。用户现在看到 `src/Foo.ets:12:3` 仍要手动复制路径或切回编辑器定位。`cr browse` 要替代 IDE，需要一个最小 Problems 面板，把当前任务输出中的通用文件锚点收起来并支持打开。

## What Changes

- 新增 `task problems` / `problems` 命令，打开当前任务输出的 Problems 页。
- 从当前 `TaskState.lines` 中识别通用 `path:line[:column]` 和 repo 内绝对路径锚点。
- Problems 页展示匹配到的文件、行列和原始日志摘要。
- Problems 页支持 ↑/↓、PgUp/PgDn、Home/End 选择，Enter 打开选中位置到编辑器。
- 页面进入 browser page history，`b` 返回来源页。
- 不解析 severity、不支持多种专有编译器格式、不搜索历史任务、不持久化 problems。

## Capabilities

### New Capabilities
- `task-problems-page`: 从当前任务输出中提取文件位置，并在 TUI 内列出和打开。

### Modified Capabilities
- `browser-page-navigation`: 导航栈支持 Task Problems 页。
- `task-output-detail-page`: Task Output 页的 action bar 暴露 Problems 入口。

## Impact

- 新增 `cr.ui.task_problems` 纯解析/展示模型。
- 影响 `cr.ui.navigation`、`cr.ui.commands`、`cr.ui.command_catalog`、`cr.ui.page_content`、`cr.ui.browser`。
- 复用 `cr.ui.file_actions.open_path` 作为编辑器打开边界。
- 不改变 task runtime、output capture、workspace persistence 或 Git review scope。
