## 为什么

`cr browse` 的底部面板已经从单一 build 扩展到 build/test/lint，但核心运行时仍叫 `BuildState`，主循环字段仍叫 `state.build`，轮询和记录函数也仍叫 `_poll_build` / `_record_completed_build`。这些名字会让后续继续增加 task 类型、拆模块或换语言时产生错误心智模型。

本轮把后台任务运行时命名收敛到 `Task`：代码主链路表达“当前后台任务”，build 只保留在 build 命令配置和用户可见 build 任务文案里。

## 改什么

- 将实时后台任务状态从 `BuildState` 重命名为 `TaskState`。
- 将 `BrowserState.build` 重命名为 `BrowserState.task`。
- 将任务面板和生命周期 helper 从 build 命名改为 task 命名，例如 `_poll_task`、`_record_completed_task`、`_task_panel_lines`。
- 保留用户命令行为：`: build`、`: test`、`: lint`、`: stop`、`: rerun` 不变。
- 保留 build 命令发现函数 `_build_command`，因为它确实只负责 build 默认命令。

## 不做

- 不新增用户功能。
- 不引入并发任务、任务队列或 task tabs。
- 不移动文件或拆出新模块。
- 不改变底部面板布局、刷新策略、停止/强杀语义或历史记录行为。
