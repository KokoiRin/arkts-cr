## Context

当前 `BuildState` 同时表示当前 build 进程、输出行和渲染缓存。`BrowserState.build` 保存当前/最近 build；面板由 `_build_panel_lines()` 直接从 `BuildState` 渲染。

要支持任务历史，不能把历史塞进 build log lines。日志是输出流，history 是结构化任务事实；两者应该分开。考虑到目前只有 build 一种后台任务，不需要抽象成通用 task manager。

## State

新增：

- `TaskRecord`: `kind`、`status`、`command`、`returncode`
- `BrowserState.task_history: list[TaskRecord]`
- `BuildState.history_recorded: bool`

`history_recorded` 防止 idle polling 重复记录同一次完成的 build。

## Behavior

- `_poll_build(build)` 仍负责更新 build state 和日志。
- 新增 `_record_completed_build(state)`：当 `state.build.returncode` 已经有值且未记录时，把 compact task record append 到 `state.task_history`。
- `run_browser` 每轮 poll 后调用 `_record_completed_build(state)`。
- `_build_panel_lines()` 接收可选 history，在状态行下方渲染最近 2-3 条任务结果；如果空间不足，优先保留当前任务状态和最新日志。

## Boundaries

- 不持久化 task history。
- 不支持并发任务。
- 不新增 test/lint 命令。
- 不改变 build stop / rerun / force kill 生命周期。

## Test Plan

- 单元测试：build panel 渲染 recent task history。
- 单元测试：completed build 只记录一次。
- 单元测试：rerun 后仍能看到前一次 build history。
- 全量测试保证 build stop/rerun 旧行为不变。
