## Why

`cr browse` 已经有主内容区、build 任务面板和输入提示行，但真实使用里仍然会出现后台 build 日志刷新后，用户再导航、打开文件或输入命令时屏幕被打乱的问题。根因是当前有多个独立输出入口：整屏重画、build 面板局部刷新、临时输入 prompt 和普通错误提示都可以直接写终端，却没有一个统一的 browser frame 来声明“当前哪些区域已经被谁画过”。

这个问题会阻碍长期目标：`cr` 要成为替代 IDE 高频操作的 terminal workbench。后续继续加入 test、lint、搜索、AI 操作、commit 操作时，如果没有清晰的页面层级和刷新所有权，功能越多体验越乱。

## What Changes

- 为 raw-key browser 引入显式 frame 状态，统一记录最后一次屏幕布局、主内容帧、任务面板帧和 prompt 行。
- 全屏重画和 build 局部刷新共享同一套 frame 状态；局部刷新只能在当前 layout 仍然匹配时发生。
- 用户操作触发主内容变化时，下一帧重新绘制完整 browser frame，并同步更新任务面板快照，避免旧 build 刷新覆盖新页面。
- 临时 line input（`:` command、`/` filter）结束后，必须让下一帧恢复固定 browser frame。
- 文档把页面模型从“四个区域”升级成“一个 frame、四个区域、一个后台任务面板”，明确后续功能应该落在哪层。

## Capabilities

### New Capabilities
- `browser-frame-rendering`: raw-key browser 的统一屏幕帧、局部刷新安全条件和页面层级。

### Modified Capabilities
- `browser-screen-layout`: 继续使用现有 layout helper，但由 frame 状态拥有当前布局和刷新边界。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 raw-key 渲染循环、build panel 局部刷新和临时输入恢复。
- 测试需要覆盖 full redraw 后的 build panel 快照同步、layout 变化时禁止旧 panel 局部刷新、line input 返回后强制恢复 frame、以及页面层级文档。
- 不引入第三方 TUI 框架，不改变非 TTY 行模式。
