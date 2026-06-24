## Why

`cr browse` 已经具备基本 TUI 形态，但大 review 中仍需要用户通过上下键线性查找文件；文件数量一多，定位目标文件会变慢。与此同时，`src/cr/cli.py` 已经承担参数解析、Git 选择、TUI 状态机、屏幕绘制、打开编辑器等多种职责，module interface 变浅，继续加体验能力会降低 locality。

## What Changes

- 为 `cr browse` 增加列表内搜索过滤能力：用户按 `/` 输入关键字后，只显示匹配路径的改动文件。
- 在交互界面中展示当前过滤条件和匹配数量，并支持清除过滤条件。
- 保留现有键盘导航、数字选择、打开编辑器、刷新、非 TTY 行模式兼容行为。
- 将 browse/TUI 的状态机和渲染逻辑从 `cli.py` 中拆出到更深的 module，降低 CLI 入口复杂度。
- 不引入第三方 TUI 依赖；继续使用标准库和现有终端渲染策略。

## Capabilities

### New Capabilities
- `interactive-review-navigation`: 交互式 review browser 的文件选择、过滤、导航和打开文件行为。

### Modified Capabilities
- 无。

## Impact

- 主要影响 `src/cr/cli.py` 和新增的 browse/TUI module。
- 测试需要覆盖过滤行为、非 TTY 兼容、状态刷新与现有导航行为不回退。
- README 和 P0 文档需要更新，明确新的搜索过滤操作和架构拆分方向。
