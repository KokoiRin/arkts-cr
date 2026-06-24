## Why

Task Panel 已经承载 build / test / lint、停止、重跑、输出采集和历史记录，但这些 runtime 规则仍散在 `src/cr/ui/browser.py`。继续往 IDE-like workbench 增加更多常用操作时，任务生命周期会成为高耦合点，影响体验稳定性和后续迁移。

## What Changes

- 新增 `cr.ui.tasks` task runtime module，承载任务命令解析、后台进程启动、输出采集、停止、强杀升级、前台运行和历史记录。
- 让 `browser.py` 通过 task runtime interface 管理任务，不再直接拥有 task lifecycle helper。
- 保留 Task Panel 渲染、Browser Frame 布局、用户命令、环境变量和 DouyinHarmony build 默认行为。
- 保留 `TaskState` / `TaskRecord` 作为浏览器可用的数据模型，但其权威定义移动到 task runtime module。
- 不新增任务种类，不实现 task preset 配置，不改变 `.git/cr/browse-state.json`。

## Capabilities

### New Capabilities

- `browser-task-runtime`: 定义浏览器 Task Panel 背后的任务 runtime 如何解析命令、启动/轮询/停止/重跑任务、收集输出并记录历史。

### Modified Capabilities

无。

## Impact

- 影响 `src/cr/ui/browser.py` 和新增 `src/cr/ui/tasks.py`。
- 需要更新当前直接 import `cr.ui.browser` task helper 的测试，使任务 runtime 行为通过 `cr.ui.tasks` interface 验证。
- 无新增运行时依赖，无用户命令、CLI 参数、环境变量或持久化格式变化。
