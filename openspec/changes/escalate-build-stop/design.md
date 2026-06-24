## Context

后台 build 已经有固定底部面板、`stop` / `rerun` 控制，以及进程组生命周期边界。剩下的风险是：`SIGTERM` 只是请求退出，不保证构建工具真的退出。

当前浏览器主循环每次都会调用 `_poll_build(state.build)`，这是最小合适的 escalation 落点：不需要新线程、不需要通用任务调度器，也不会影响用户键盘导航。

## Design

### 状态字段

`BuildState` 新增：

- `stop_requested_at: float | None`：调用 `stop` 时的 `time.monotonic()`。
- `stop_escalated: bool`：是否已经发送过强杀信号。

保留 `stop_requested` 作为状态语义，用于面板显示 `stopping` / `stopped`。

### 宽限期

新增模块常量：

```python
BUILD_STOP_KILL_GRACE_SECONDS = 2.0
```

2 秒足够给正常 build 捕获 SIGTERM 并退出，同时不会让用户长期卡在 stopping。后续如果真实仓库需要配置化，再扩展 CLI 参数；本 change 不提前做配置项。

### escalation 行为

`_poll_build` 在 drain output 和 poll 之后检查：

1. build 仍在运行。
2. `stop_requested` 为 true。
3. `stop_requested_at` 已设置。
4. 尚未 `stop_escalated`。
5. 当前时间超过宽限期。

满足后对 `process_group_id` 发送 `SIGKILL`；如果没有进程组能力，则 fallback 到 `process.kill()`。无论哪种路径，都只执行一次，并向 build 日志追加一行可读文案。

## Non-goals

- 不新增通用 background task manager。
- 不新增用户可配置 grace 参数。
- 不改变 foreground build。
