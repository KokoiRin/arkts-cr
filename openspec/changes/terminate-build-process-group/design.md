## Context

`cr browse` 的后台 build 是当前产品里第一个长期运行的后台任务。前面已经解决了“输出固定在底部面板”和“用户可以 stop/rerun”，但进程生命周期仍然偏薄：`subprocess.Popen(...).terminate()` 只覆盖父进程，不覆盖 build 命令再创建的子进程。

这对 `./remote buildEntry --app douyin` 这类入口尤其危险，因为真正输出日志的可能不是入口进程本身。

## Design

### 进程组作为 build 的生命周期边界

后台 build 使用 `subprocess.Popen(..., start_new_session=True)` 启动。这样每次 build 都拥有自己的 session / process group，`cr` 可以用父进程 pid 作为 pgid 来停止整组进程。

`BuildState` 记录 `process_group_id`：

- 正常后台 build：`process_group_id = process.pid`
- 启动失败或 idle 占位 build：`process_group_id = None`

### 停止策略

`_stop_build` 保持同步、轻量：

1. 如果没有 build 或 build 不在运行，沿用当前反馈。
2. 标记 `stop_requested`，追加 `Stopping build...`。
3. 如果存在 `process_group_id`，调用 `os.killpg(process_group_id, signal.SIGTERM)`。
4. 如果进程组终止失败，追加错误文案，并 fallback 到 `process.terminate()`。

暂不在同一次 change 里实现超时后 `SIGKILL`。原因是当前事件循环没有通用定时任务模型；加入强杀计时会扩大状态机。这个能力可以作为后续 P0，在确认真实残留后做。

### 平台边界

项目当前运行环境以 macOS / POSIX 终端为主，`os.killpg` 和 `start_new_session=True` 可用。为了避免破坏其他平台，代码会做能力检查：没有进程组能力时退回父进程终止，并在测试中覆盖 fallback。

## Alternatives

- 只继续 `process.terminate()`：不能覆盖子进程，不能解决用户反馈的底层风险。
- 引入通用 task manager：现在只有 build 一个后台任务，抽象过早。
- 立即加入 SIGKILL 超时升级：更完整，但会引入时间状态和额外轮询复杂度，本 change 先解决最关键的进程组边界。

## Verification

- 单元测试验证 build 启动时记录进程组。
- 行为测试验证 stop 会终止父进程和子进程。
- fallback 测试验证进程组终止失败时，build 面板出现可读错误并尝试父进程终止。
- 全量 `unittest`、`compileall`、`openspec validate --strict`。
