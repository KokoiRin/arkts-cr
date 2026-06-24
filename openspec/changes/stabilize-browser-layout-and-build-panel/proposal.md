## Why

`cr browse` 已经开始承担 IDE 替代入口的角色，但 build 日志面板和键盘操作共享同一块终端输出区域，导致 build 更新后再导航、打开文件或输入命令时容易把屏幕打乱。现在需要先把 TUI 页面层级固化下来，否则后续继续增加 build、commit、搜索、打开编辑器等常用操作时，体验会继续被刷新细节拖垮。

## What Changes

- 为 browser 引入明确的屏幕层级：顶部帮助/上下文、主内容区、底部任务面板、最底部输入提示。
- build 日志只占用底部任务面板，后台更新不能滚动主内容，也不能挤压输入提示。
- raw-key 模式下普通按键不再额外输出换行；所有导航和页面切换通过固定屏幕区域重绘完成。
- 文档记录当前产品形态：`cr` 是面向代码 review 和常用仓库操作的 terminal workbench / lightweight TUI，而不是一次性命令输出。
- 保留非 TTY 行模式兼容；不引入第三方 TUI 框架。

## Capabilities

### New Capabilities
- `browser-screen-layout`: 交互式 browser 的页面层级、固定屏幕渲染、底部任务面板和输入提示行为。

### Modified Capabilities
- 无。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的屏幕布局、raw-key 输入和 build 面板渲染。
- 测试需要覆盖 build 面板存在时的主区/输入区边界、局部刷新不清屏不滚屏、raw-key 命令不额外换行。
- README、`docs/design.md` 和 `docs/p0.md` 需要更新，记录产品定位和当前页面层级。
