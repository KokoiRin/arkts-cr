## Context

Task Panel 已经承载 build/test/lint 的后台输出、状态和历史摘要，但输出内容目前只能靠终端选择复制。IDE 的 Output Panel 通常支持复制日志、保存日志、把失败信息交给其他工具；`cr browse` 需要同类能力，先从当前任务输出 handoff 做起。

当前分层中，`cr.ui.tasks` 拥有任务 runtime 状态与命令展示规则；`cr.ui.frame` 只负责 panel 渲染；`cr.ui.file_actions` 和 `cr.ui.handoff` 已经分别拥有剪贴板和文件保存边缘能力。

## Goals / Non-Goals

**Goals:**

- `copy task` 复制当前任务的 handoff 文本。
- `save task [PATH]` 保存当前任务的 handoff 文本，默认到 `.cr/handoff/task-output.md`。
- handoff 文本包含任务类型、状态、命令和当前捕获的输出行。
- 当前任务不存在时给出空状态，不调用剪贴板或写文件。
- 命令进入 parser、command catalog、command palette 和 contextual action bar。

**Non-Goals:**

- 不解析 task 输出里的错误位置。
- 不新增 `open issue` / `next issue` 诊断导航。
- 不保存 task history 或 task output 到 workspace persistence。
- 不改变后台 task 生命周期、停止逻辑或输出捕获策略。

## Decisions

1. **任务输出文本由 Task Runtime 生成。**
   - 选择：在 `cr.ui.tasks` 增加纯函数，把 `TaskState` 转成 Markdown handoff 文本。
   - 理由：任务类型、状态、命令和输出行都属于 Task Runtime 知识；Browser 不应该重新拼 task 语义。
   - 替代方案：在 `browser.py` 直接读取 `TaskState` 拼文本。拒绝，因为会让 Browser Action Execution 承载任务输出格式。

2. **copy/save 是 Browser Action Execution 的边缘编排。**
   - 选择：parser 产生 `COPY_TASK_OUTPUT` / `SAVE_TASK_OUTPUT` action，executor 调用 `tasks` 生成文本，再调用 `file_actions.copy_text` 或 `handoff.save_task_text`。
   - 理由：剪贴板和文件写入是 UI edge side effect，已有 pattern 也是 executor 展示返回消息。

3. **保存路径复用 UI handoff 模块。**
   - 选择：给 `cr.ui.handoff` 增加 task output 默认路径和保存 helper。
   - 理由：默认路径、repo-relative path、父目录创建、错误消息已经集中在该模块。

4. **当前任务为空时不 fallback 到历史。**
   - 选择：只 handoff 当前 `state.task`，没有当前任务则返回 `No task output to copy/save.`
   - 理由：`TaskRecord` 只保存摘要，不保存完整输出；为了避免误导，不从历史重建不存在的日志。

## Risks / Trade-offs

- **长日志复制可能很大** → 当前 TaskState 已经只保留 runtime 捕获的 `lines`，本功能不扩大捕获容量。
- **运行中日志仍在变化** → 命令复制/保存调用时刻的快照，状态文本显示当前状态。
- **空输出也需要可用** → 如果有当前任务但尚无输出，handoff 文本包含 `(no output captured)`，方便用户知道命令已触发。
- **未来诊断导航需要更多结构** → 本次只建立 handoff 文本接口，不提前设计诊断模型。
