## Why

`cr browse` 已经把 build 输出固定到底部任务面板，但当前 `stop` 只终止 build 入口进程。如果 build 命令再拉起子进程，父进程退出后子进程仍可能继续输出或占用资源，用户继续浏览代码时就会再次遇到日志干扰界面的问题。

要让 `cr` 更像一个可靠的 terminal workbench，后台 build 必须有清晰的生命周期边界：启动时归属到独立进程组，停止时收口整个进程组，并在无法收口时给出可见反馈。

## What Changes

- interactive browser 启动后台 build 时，为 build 创建独立进程组。
- `stop` / `cancel` 停止 build 时，优先终止整个进程组，而不是只终止父进程。
- 如果进程组终止失败，退回到父进程终止并把失败原因写入 build 面板。
- 保留当前 build 面板、状态文案、foreground build 和命令发现规则。
- 不引入通用任务管理器；该能力仍然局限在 `BuildState`。

## Capabilities

### New Capabilities
- `build-process-group-lifecycle`: 后台 build 的进程组启动、停止和失败反馈行为。

### Modified Capabilities
- `build-task-controls`: `stop` / `cancel` 的停止范围从父进程扩展为整个 build 进程组。

## Impact

- 主要影响 `src/cr/ui/browser.py` 中 `_start_build`、`_stop_build` 和 `BuildState`。
- 测试需要覆盖进程组启动、停止整组、终止失败时的 fallback 文案。
- 文档需要说明 `stop` 会收口 build 进程组，减少残留构建输出。
