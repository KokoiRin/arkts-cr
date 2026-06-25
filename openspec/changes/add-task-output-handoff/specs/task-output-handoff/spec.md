## ADDED Requirements

### Requirement: 复制当前任务输出
系统 SHALL 支持在浏览器内复制当前 Task Panel 的任务输出 handoff 文本。

#### Scenario: Copy running task output
- **WHEN** 当前存在正在运行的 build/test/lint task 且用户执行 `copy task`
- **THEN** 系统 SHALL 复制包含任务类型、状态、命令和当前输出行的文本

#### Scenario: Copy completed task output
- **WHEN** 当前 task 已完成且用户执行 `copy task`
- **THEN** 系统 SHALL 复制包含完成状态、命令和捕获输出行的文本

#### Scenario: Copy without task
- **WHEN** 当前没有 task 且用户执行 `copy task`
- **THEN** 系统 SHALL 报告没有 task output 可复制，并且 MUST NOT 调用剪贴板命令

### Requirement: 保存当前任务输出
系统 SHALL 支持在浏览器内保存当前 Task Panel 的任务输出 handoff 文本。

#### Scenario: Save task output to default path
- **WHEN** 当前存在 task 且用户执行 `save task`
- **THEN** 系统 SHALL 将 task output 写入 `.cr/handoff/task-output.md`

#### Scenario: Save task output to custom path
- **WHEN** 当前存在 task 且用户执行 `save task tmp/build.md`
- **THEN** 系统 SHALL 将 task output 写入用户指定路径

#### Scenario: Save without task
- **WHEN** 当前没有 task 且用户执行 `save task`
- **THEN** 系统 SHALL 报告没有 task output 可保存，并且 MUST NOT 写入文件

### Requirement: 任务输出 handoff 不改变任务运行时
系统 MUST 将 task output handoff 作为命令副作用处理，不改变 task lifecycle、task history 或 workspace persistence。

#### Scenario: Command parsing remains explicit
- **WHEN** 用户输入 `copy task` 或 `save task`
- **THEN** command parser SHALL 返回专用 task output handoff action

#### Scenario: Workspace persistence unchanged
- **WHEN** 浏览器保存 workspace state
- **THEN** persisted data SHALL NOT include task output handoff content
