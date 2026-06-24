## Context

现有实现里，`_draw_browse_screen()` 会清屏并重画主内容、build 面板和 prompt；`_draw_build_panel_only()` 会在 idle tick 时只重画底部 build 面板。两者都调用 `_screen_layout()`，但只有 `BuildState.last_rendered_panel` 记录了局部面板内容，没有记录上一次完整 frame 的 layout、prompt 行和 build 区域是否仍然有效。

因此真实终端里会出现三类不稳定：

- 完整重画刚改变了页面布局，旧的 build panel 局部刷新仍然可能按当前 build 状态写底部区域。
- line input 暂时把光标和文字带到 prompt 区外，返回后如果只发生局部 build 刷新，主 frame 没有被恢复。
- 后续新增 test/lint/search 等任务面板时，会继续复制 `_draw_build_panel_only()` 的模式，输出所有权更散。

## Goals / Non-Goals

**Goals:**

- 引入小型 `BrowserFrame` 状态对象，让 raw-key 模式有唯一的屏幕帧事实来源。
- 全屏重画后记录 layout、prompt、build panel 内容和一个递增 frame id。
- build 局部刷新前验证当前 layout 仍然匹配上一次完整 frame；否则跳过局部刷新并要求下一次全屏重画。
- line input 结束后统一标记 frame dirty，避免停留在半输入状态时只刷新底部日志。
- 在 README / design / P0 中把产品页面模型讲清楚：`cr` 是一个 terminal workbench，当前页面由固定 frame 管理，不是 stdout 日志流。

**Non-Goals:**

- 不引入 Textual、prompt_toolkit、curses 等框架。
- 不实现多后台任务队列；本轮仍只有 build 面板。
- 不改变 build 命令、stop/rerun 语义。
- 不改变非 TTY 行模式。

## Decisions

### Decision: BrowserFrame 只管理渲染状态，不管理业务状态

`BrowserState` 仍然管理文件、scope、selection、build 等业务状态。新增的 frame 状态只回答“上一次 raw-key 屏幕画成了什么布局，以及局部刷新是否安全”。这样避免把 UI 缓存和 review 状态混在一起。

### Decision: 局部刷新必须依赖最近一次完整 frame

`_draw_build_panel_only()` 不能独立决定自己可以写哪几行。它应接收 frame 状态并验证：

- 已经发生过完整 frame render。
- 当前 `_screen_layout(build)` 与 frame 中记录的 layout 相同。
- build 面板区存在且高度一致。

不满足时返回 `False`，调用方设置 `needs_redraw = True`，让下一轮完整 frame 恢复页面。

### Decision: 全屏重画同步任务面板快照

完整 frame render 会同时画主内容、任务面板和 prompt，所以它也必须更新 `BuildState.last_rendered_panel`。否则下一次 idle tick 会以为面板没画过，重复写一帧，造成闪烁。

### Decision: 临时 line input 后恢复 frame

`:` 和 `/` 这类 line input 可以暂时使用普通终端输入，但返回后必须让 raw-key loop 走完整 frame render。这样即使用户输入期间 build 输出已经变化，也不会只靠局部刷新修补屏幕。

## Test Plan

- 单元测试：完整 frame render 后，后续 build panel 局部刷新在内容相同时不输出。
- 单元测试：如果 frame layout 过期，build panel 局部刷新不写终端，并向调用方报告需要 full redraw。
- 单元测试：command/filter line input 返回后，raw-key loop 标记 full redraw。
- 集成测试：build tick 后再执行导航命令，会走 full redraw 并保持 prompt 在最后一行。

## Risks / Trade-offs

- [Risk] 增加 frame 状态后，渲染调用签名会变长。Mitigation：只把 frame 传给 raw-key 渲染边界，不传入业务渲染函数。
- [Risk] 跳过局部刷新可能让某一次 build 输出晚一帧显示。Mitigation：layout 不匹配时完整重画会马上恢复正确画面，体验优先于抢一行日志。
