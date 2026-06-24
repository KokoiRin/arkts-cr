## 设计

这是一次命名和主模型收敛，不是行为扩展。当前 `src/cr/ui/browser.py` 仍然是唯一的 interactive browser adapter，本轮不拆模块，避免把纯重命名升级成架构迁移。

## 命名边界

- 通用任务运行时使用 `TaskState`。
- 浏览器当前后台任务字段使用 `state.task`。
- 面板 helper 使用 `task_panel` 命名。
- 生命周期 helper 使用 `task` 命名：start/stop/rerun/poll/record/drain/escalate。
- build 专属命令解析继续叫 `_build_command`，因为 DouyinHarmony 默认命令只适用于 build。
- 旧 build-specific helper 不作为主链路继续使用；如需要短期兼容测试导入，只能是薄 wrapper 或 alias。

## 行为保持

- `build` / `compile` 仍启动 build 任务。
- `test` / `tests` 仍启动 test 任务。
- `lint` 仍启动 lint 任务。
- `stop` / `cancel`、`rerun` / `rebuild` 行为不变。
- 面板高度、局部刷新、frame dirty 检查、输出截断和任务历史不变。
- 行模式前台运行行为不变。

## 测试策略

- 先增加命名约束测试，确保核心模块不再导出或引用 `BuildState` 作为主模型。
- 现有行为测试继续覆盖 build/test/lint、停止、强杀、rerun、面板刷新和行模式。
- 重命名后跑全量单元测试和编译检查，证明行为没有被改坏。

## 风险

- 机械重命名容易漏掉测试或文档中的旧名字。
- 旧 P0 历史条目会保留 build 文案，因为它们描述当时的 feature；当前设计文档和架构风险需要更新到 task 命名。
