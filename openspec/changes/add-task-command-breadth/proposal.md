## 为什么

`cr browse` 已经有稳定的底部后台任务面板，但目前只有 `build` 能使用这块区域。作为 terminal workbench，它要逐步承接 IDE 高频操作，用户在 review 过程中最常见的下一步通常不是只有编译，还包括跑测试和跑 lint。

本轮把任务入口从单一 build 扩到 build/test/lint：用户可以在不离开 changed-file list 或 file diff 的情况下启动测试或 lint，看 5-10 行实时输出，必要时停止或重跑最近任务。

## 改什么

- 新增 `test` / `tests` 命令，通过同一个后台任务面板运行配置好的 test 命令。
- 新增 `lint` 命令，通过同一个后台任务面板运行配置好的 lint 命令。
- 新增 `--test-cmd` / `CR_TEST_CMD` 和 `--lint-cmd` / `CR_LINT_CMD` 配置。
- `stop` / `cancel` 停止当前正在运行的后台任务。
- `rerun` / `rebuild` 重跑最近启动的后台任务，而不是固定重跑 build。
- command palette 和 README 显示 build/test/lint 任务入口。

## 不做

- 不实现多个后台任务并发运行。
- 不实现任务队列或独立 task tabs。
- 不自动猜测所有项目的 test/lint 命令；本轮只支持显式配置。
- 不把 `BuildState` 全量重命名为 `TaskState`；本轮先在现有生命周期上扩展行为，避免一次性 churn。
