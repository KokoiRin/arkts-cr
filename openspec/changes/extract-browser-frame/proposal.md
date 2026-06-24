## Why

`browser.py` 已经从 ReviewWorkspace、Command Catalog、Task Runtime、Workspace Persistence 中拆出了多块产品语义，但仍直接拥有 Browser Frame 的布局计算、Task Panel 行渲染、局部刷新缓存判断和 ANSI 刷新细节。随着工作台继续替代 IDE 的构建、测试、导航和文件操作体验，这些屏幕层规则需要成为单独模块，避免继续挤压浏览器主循环。

## What Changes

- 新增 `cr.ui.frame` 模块，拥有 Browser Frame 的屏幕布局、Task Panel presentation、终端行裁剪、局部刷新输出和 frame cache 状态。
- `browser.py` 保留产品页面内容渲染、输入循环、命令执行和具体页面行生成，但通过兼容包装委托屏幕层 helper。
- 保持 raw-key 全屏重绘、Task Panel 局部刷新、prompt 行位置、5-10 行 task panel 高度、history 显示、dirty frame 拒绝局刷等行为不变。
- 更新架构文档和 P0 记录，让后续渲染/输入或语言迁移有明确接缝。

## Capabilities

### New Capabilities

- `browser-frame-rendering-module`: Browser Frame / Task Panel 屏幕层模块的职责、兼容行为和测试要求。

### Modified Capabilities

- 无。

## Impact

- 影响 `src/cr/ui/browser.py`、新增 `src/cr/ui/frame.py`、现有 browser frame/task panel 测试、`CONTEXT.md`、`docs/design.md`、`docs/workbench-navigation.md` 和 `docs/p0.md`。
- 不改变用户命令、任务运行时、Review Scope / Changed Files / File Detail 产品层级、workspace persistence schema 或 CLI 参数。
