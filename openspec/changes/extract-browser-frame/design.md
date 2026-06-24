## Context

`cr browse` 的产品导航层已经明确为 `Review Scope -> Changed Files -> File Detail`，屏幕渲染层也明确为 context/status、main content、background task panel、input prompt。当前 `browser.py` 仍直接拥有 `ScreenLayout`、`BrowserFrame`、Task Panel 行渲染、行宽裁剪和局部刷新 ANSI 输出。

这部分逻辑不是产品页面内容，也不是任务运行时。它的变化风险主要在体验稳定性：全屏重绘不能闪、Task Panel 局部刷新不能清屏、prompt 行必须固定、dirty/stale frame 时必须拒绝局刷并等待完整重绘。

## Goals / Non-Goals

**Goals:**

- 新增 `cr.ui.frame`，作为 Browser Frame / Task Panel presentation 的单一拥有者。
- 保持现有 `browser.py` 私有 helper 名称作为兼容包装，降低测试和调用点的一次性改动量。
- 保持 Task Panel 高度、history 行、waiting 提示、ANSI 局刷和 frame dirty/cache 行为不变。
- 更新架构术语，让屏幕层后续可以继续独立演进。

**Non-Goals:**

- 不重写 Changed Files、File Detail、Scope Home、Commit Picker、Command Palette 的页面内容生成。
- 不改变 `cr.ui.tasks` 的 process lifecycle、output capture、stop/rerun 或 history 记录。
- 不引入 curses、Textual、Rich live display 或其他新终端框架。
- 不改变用户命令、prompt 文案或 workspace persistence 格式。

## Decisions

1. **抽 `cr.ui.frame`，不抽完整 renderer**

   `browser.py` 仍然知道“当前页面应该生成哪些主内容行”，因为这些行依赖 Review Scope、Git facts、file detail cache 和 command palette state。`cr.ui.frame` 只拥有屏幕区域和 Task Panel presentation：`ScreenLayout`、`BrowserFrame`、`screen_height`、`screen_layout`、`task_panel_lines`、`draw_task_panel_only`、`fit_terminal_line`。

   备选方案是把 `_draw_browse_screen` 整体搬走，但那会把页面内容依赖也搬进新模块，形成更宽、更浅的接口。

2. **兼容包装先保留在 `browser.py`**

   现有测试和内部调用使用 `_screen_layout`、`_task_panel_lines`、`_draw_task_panel_only` 等私有 helper。短期保留这些函数作为委托包装，能证明用户行为和测试行为不变，同时让新模块先拥有实现。

   后续如果需要更大迁移，可以逐步把测试改为直接覆盖 `cr.ui.frame`，再删除包装。

3. **Task Panel 仍依赖 `TaskState` / `TaskRecord`，不反向依赖 browser state**

   `cr.ui.frame` 可以依赖 `cr.ui.tasks` 和 `cr.ui.terminal`，但不能依赖 `BrowserState`、ReviewWorkspace、navigation 或 command parsing。这样它保持屏幕层局部性，后续可以替换终端输出实现。

## Risks / Trade-offs

- **Risk:** 只抽 Task Panel/frame helper，`browser.py` 仍然较大。  
  **Mitigation:** 这是有意的最小切片；主内容页面渲染需要单独设计，不和本轮混做。

- **Risk:** 兼容包装让新旧函数名短期并存。  
  **Mitigation:** 包装只做委托，不保留第二份逻辑；OpenSpec 和文档明确 `cr.ui.frame` 是实现 owner。

- **Risk:** ANSI 局部刷新行为容易被重构改坏。  
  **Mitigation:** 保留并补充 frame module 测试，覆盖不清屏、stale/dirty 拒绝局刷、相同 panel 不重复输出。
