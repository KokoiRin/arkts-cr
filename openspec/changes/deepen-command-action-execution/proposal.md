## Why

`cr browse` 已经把命令字符串解析成 `BrowserCommandAction`，但 `run_browser` 仍然直接拥有每个 action 的执行分支。继续添加 IDE-like 操作时，这个主循环会重新变成高耦合入口，难以测试、迁移或替换实现语言。

## What Changes

- 增加一个浏览器 command action execution interface，将 parsed action 的执行结果表达为稳定的结果对象。
- 让 `run_browser` 把 parsed command 交给执行 interface，并根据执行结果决定继续、退出、重绘或保持等待。
- 保留现有用户命令、command palette、help 文案、raw-key sentinel、任务执行、scope 切换和导航行为。
- 不新增新的用户可见命令，不实现真实 page stack，不改变任务配置方式。

## Capabilities

### New Capabilities

- `browser-command-action-execution`: 定义 parsed browser command action 如何通过一个执行 interface 改变浏览器状态和返回 loop 控制结果。

### Modified Capabilities

无。

## Impact

- 影响 `src/cr/ui/browser.py` 的 command action 执行结构。
- 可能新增或扩展 `cr.ui` 内部模块，用于承载 action execution 的结果类型和执行入口。
- 单元测试覆盖 action execution 的 loop control、重绘结果、退出结果和现有命令行为兼容。
- 无新增运行时依赖，无 CLI 参数或持久化格式变化。
