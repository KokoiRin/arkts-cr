## Why

`cr browse` 已经可以在底部 Task Panel 中运行 build/test/lint，但用户遇到失败日志时仍需要手动框选终端文本。要替代 IDE 的 Output Panel，任务输出需要能从 workbench 内直接复制或保存，方便贴给 AI、同事或后续工具处理。

## What Changes

- 增加 `copy task` 命令，复制当前任务的命令、状态和最近输出。
- 增加 `save task [PATH]` 命令，把同样的任务输出写入文件，默认写入 `.cr/handoff/task-output.md`。
- 命令可在任务运行中或完成后使用；没有当前任务时报告空状态，不执行剪贴板或写文件。
- 命令进入 command catalog、command palette 和 contextual action bar。
- 不解析错误位置、不打开诊断、不改变 Task Panel 生命周期或历史持久化。

## Capabilities

### New Capabilities
- `task-output-handoff`: 从当前 Task Panel 复制或保存任务输出。

### Modified Capabilities

## Impact

- 影响 `cr.ui.tasks` 的任务输出文本格式。
- 影响 `cr.ui.commands`、`cr.ui.command_catalog`、`cr.ui.browser` 的命令路由。
- 复用 `cr.ui.file_actions.copy_text` 和 `cr.ui.handoff` 的剪贴板/文件保存能力。
- 不新增外部依赖，不改变 `.git/cr/browse-state.json` schema。
