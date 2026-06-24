## 设计

当前 `src/cr/ui/browser.py` 已经拥有一条完整的后台 build 生命周期：命令发现、后台进程、底部面板、局部刷新、停止、强杀、历史记录和前台行模式。`TaskRecord` 已经是通用任务命名，但实时状态仍叫 `BuildState`。

本轮采用最小扩展：保留 `BuildState` 作为现有 runtime container，给它增加 `kind` 字段，并把命令解析改成按 task kind 选择命令。这样 `test/lint` 可以复用进程组、停止、强杀、面板刷新和历史能力，同时避免在行为还少时大范围重命名。

## UI 行为

- `build` / `compile` 启动 build 任务。
- `test` / `tests` 启动 test 任务。
- `lint` 启动 lint 任务。
- `stop` / `cancel` 停止当前任务。
- `rerun` / `rebuild` 重跑最近启动的任务；如果最近任务是 test，则 rerun test；如果是 lint，则 rerun lint。
- raw-key TUI 中后台任务仍显示在底部 5-10 行面板，主工作区可继续浏览。
- 行模式中任务仍以前台方式运行并打印结果。

## 命令配置

- build：继续使用 `--build-cmd` / `CR_BUILD_CMD`，并保留 DouyinHarmony 默认 `./remote buildEntry --app douyin`。
- test：使用 `--test-cmd` / `CR_TEST_CMD`。
- lint：使用 `--lint-cmd` / `CR_LINT_CMD`。
- test/lint 未配置时，面板显示清楚的配置提示；不做猜测，避免误跑耗时或有副作用的仓库命令。

## 架构取舍

- `BuildState.kind` 是局部兼容层：它让面板文案、历史记录、停止文案和 rerun 语义可以表达“当前任务是什么”。
- 不引入 `TaskManager`，因为目前仍然只有一个当前任务，没有并发、队列或 tabs。
- 后续如果任务入口继续增加，或者需要并发任务，再把 `BuildState` 收敛为 `TaskState` 并把任务命令解析下沉到独立模块。

## 测试策略

- 单元测试覆盖 test/lint 命令配置解析。
- 单元测试覆盖后台 test 任务输出、面板标题和历史 kind。
- 单元测试覆盖 rerun 会重跑最近任务 kind。
- 浏览器循环测试覆盖 raw-key 命令 `test` 可以启动后台任务。
- 行模式测试覆盖 `test` 可以以前台方式运行配置命令。
