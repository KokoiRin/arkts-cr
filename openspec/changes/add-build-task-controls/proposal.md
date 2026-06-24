## Why

`cr browse` 已经把 build 放进底部任务面板，但它目前只有启动能力：跑错了、跑太久了、或者想快速重跑时，用户只能退出或去终端外部杀进程。要让 `cr` 成为可靠的 terminal workbench，后台任务必须具备最基本的控制闭环。

## What Changes

- 在 interactive browser 中支持停止正在运行的 build。
- 支持重跑最近一次 build 命令，避免重复输入 `: build`。
- build 面板明确展示 running、stopping、stopped、succeeded、failed 等状态。
- 停止 build 时保留 review 主内容和底部任务面板，不退出 browser。
- 保留非 TTY 行模式下的 foreground build 行为，不引入后台任务控制。

## Capabilities

### New Capabilities
- `build-task-controls`: 交互式 browser 中 build 后台任务的启动、停止、重跑和状态展示行为。

### Modified Capabilities
- 无。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 build state、命令处理和任务面板状态文案。
- 测试需要覆盖停止运行中的 build、停止后的状态、重跑 build、运行中防止重复启动，以及 README/P0 文档更新。
- 不新增外部依赖，不改变 build 命令发现规则。
