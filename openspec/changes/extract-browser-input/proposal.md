## Why

`cr browse` 的长期方向是 terminal workbench。屏幕层、页面内容、命令目录、任务运行时和 workspace persistence 已经逐步变成独立 UI modules，但 `src/cr/ui/browser.py` 仍直接拥有 raw-key 读取、line-mode input、临时 `filter>` / `command>` prompt、idle tick sentinel，以及 EOF / interrupt sentinel。

这部分虽然不大，但它是体验稳定性的入口：按键不能乱输出换行，后台任务需要 idle tick 才能局部刷新，临时输入后 frame 必须 dirty，未来如果换 TUI 框架或语言，输入协议也应该比 browser session orchestration 更容易替换。

## What Changes

- 新增 `cr.ui.input` module，拥有 browser input protocol：raw-key 是否可用、browse command 读取、filter query 读取、command query 读取、raw escape sequence 解析，以及 sentinel 常量。
- `src/cr/ui/browser.py` 保留 `_read_*` / `_use_raw_keys` 兼容 wrapper，但实现委托给 `cr.ui.input`。
- `run_browser` 继续拥有临时 prompt 的语义处理：filter query 设置哪个 filter、command query 如何 normalize、raw-key frame dirty/needs_redraw 如何恢复。
- 不改变用户可见按键、line-mode 输入、prompt 文案、EOF/interrupt/tick 行为，或后台任务 idle refresh 行为。

## Capabilities

### New Capabilities

- `browser-input-module`: 定义 interactive browser input protocol 的 ownership 和行为保持要求。

### Modified Capabilities

- `browser-frame`: 临时 line input 后的 frame dirty/restore 行为保持在 browser run loop，但底层 input reading 由 Browser Input module 提供。
- `browser-workbench-navigation`: 当前实现映射增加 Browser Input module，降低 browser orchestration 对终端输入细节的直接 ownership。

## Impact

- Adds `src/cr/ui/input.py`.
- Touches `src/cr/ui/browser.py` to delegate input helpers while preserving compatibility wrappers and existing tests.
- Adds focused tests for the new module interface and keeps raw-key browser behavior tests passing.
- Updates CONTEXT, design, navigation roadmap, and P0 notes.
