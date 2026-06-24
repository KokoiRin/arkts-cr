## Context

当前 `cr browse` 已经形成几条内部 seam：

- `BrowserPage` 负责页面词汇。
- `BrowserNavigation` 负责页面跳转和局部 reset。
- `ReviewWorkspace` 负责 Review Scope、过滤、进度和选择状态。
- `BrowserCommandAction` / `parse_browser_command` 负责命令文本解析。

剩余摩擦在 `run_browser`：主循环仍直接执行每个 command action，导致输入读取、loop 控制、状态变化、任务生命周期、scope 切换、帮助输出和未知命令反馈混在同一个 while loop 中。下一步继续向 IDE-like workbench 扩展时，这会让每个新操作都修改同一个高风险函数。

## Goals / Non-Goals

**Goals:**

- 定义一个小的 command action execution interface：输入 parsed command，输出 loop 控制结果。
- 让 `run_browser` 只负责读取输入、处理 sentinel / 临时 prompt、调用执行器、保存退出状态和驱动渲染。
- 让 command action 的状态变化集中在一个执行器里，并拆成 focused handler。
- 保持现有用户可见行为、命令别名、help / palette 文案、raw-key 与 line-mode 行为不变。

**Non-Goals:**

- 不新增用户命令。
- 不实现真实 page stack。
- 不改变 build/test/lint 的命令来源或执行方式。
- 不把所有 UI 边缘强行搬出 `browser.py`。
- 不引入新依赖或第三方 TUI 框架。

## Decisions

### 1. 先在 `browser.py` 内建立执行器 seam

选择：新增 `BrowserCommandExecutor` 和 `BrowserActionResult`，由 `run_browser` 调用。

原因：执行器目前仍需要调用 `_show_browser_message`、`_start_task`、`_open_change`、`_switch_review_scope`、`_scroll_file` 等 UI 边缘函数。现在强行搬到独立模块会让新模块反向 import `browser.py` 私有函数，形成更薄、更脆的 seam。

替代方案：新增 `cr.ui.actions` 并把所有 handler 搬过去。暂不采用，因为这要求先把 task、editor handoff、render feedback、scope reload 等边缘能力全部端口化，超出本 P0。

### 2. 执行结果只表达 loop control

选择：`BrowserActionResult` 表达 `handled`、`needs_redraw` 和 `exit_code`。执行器可以直接改变 `BrowserState` 或调用现有边缘函数，但不能自己保存 workspace 退出状态。

原因：保存退出状态需要 `repo`，且是主 loop 生命周期职责。执行器说“要退出”，`run_browser` 决定退出前保存什么。

替代方案：执行器直接返回最终 process exit code 并保存 state。暂不采用，因为它会把生命周期和 action execution 混在一起。

### 3. Prompt 读取仍留在主 loop 输入边缘

选择：`filter_prompt`、`command_prompt` 和 command palette Enter handoff 继续在 `run_browser` 中转换为最终 parsed command，再交给执行器。

原因：这些操作是“读取下一个输入”的协议，不是普通 action。它们会临时破坏 raw-key frame，需要继续和 Browser Frame 恢复逻辑放在输入边缘。

替代方案：执行器接收 prompt reader callbacks。暂不采用，因为本轮目标是减少主循环 action 分支，而不是抽象输入协议。

## Risks / Trade-offs

- 执行器仍在 `browser.py` 内，文件体积不会立刻明显下降。→ 缓解：先让 `run_browser` 调用面变小；后续再把 task/editor/scope edge 分别端口化后外移。
- 测试可能过度绑定执行器内部。→ 缓解：测试执行结果和状态变化，不断言具体 handler 调用次数。
- 大量分支搬迁可能改变细微行为。→ 缓解：TDD 先覆盖 loop result 和代表性 action，再跑现有完整 suite。
