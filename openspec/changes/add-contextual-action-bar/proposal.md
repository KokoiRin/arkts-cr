## Why

`cr browse` 的能力已经覆盖 Review Scope、Changed Files、File Detail、Command Palette 和 Task Panel，但用户在不同页面仍需要记住大量命令。要让它更接近 IDE，界面需要持续告诉用户“当前页面最值得用的动作是什么”，而不是只依赖一整屏帮助文本或命令列表。

## What Changes

- 在 raw-key 浏览界面中增加页面相关的 contextual action bar，用一行展示当前页面的高频动作。
- 动作条随页面变化：Changed Files、File Detail、Scope Home、Commit Picker、Command Palette 显示不同操作提示。
- 动作条只展示已有命令和快捷键，不新增命令语义、不改变命令解析、不改变持久化状态。
- 动作条与现有 Browser Frame / Task Panel 共存，任务面板运行时仍保持主内容、任务面板、输入 prompt 的稳定布局。

## Capabilities

### New Capabilities
- `contextual-action-bar`: 浏览器页面根据当前层级展示高频动作提示。

### Modified Capabilities

## Impact

- 主要影响 `cr.ui.page_content` 的页面内容渲染规则。
- `cr.ui.browser` 只负责把动作条组合进 raw-key frame，不接管动作条内容。
- 测试覆盖动作条文本、页面差异、任务面板布局共存和既有命令行为不变。
- 不新增外部依赖，不改变 CLI 参数、命令解析或 workspace persistence schema。
