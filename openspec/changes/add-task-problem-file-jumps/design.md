## 行为

`next problem file` 和 `prev problem file` 只在 Task Problems 的当前可见列表上移动选择。

`next problem file` 从当前选中项之后查找第一条 `path` 不同的问题。如果找到，就把 `problem_selected` 移到那条问题；如果没有下一个文件，则保持选择不变并提示已经在最后一个文件。

`prev problem file` 从当前选中项之前反向查找第一条 `path` 不同的问题，然后继续回退到该文件在当前可见列表中的第一条问题。如果没有上一个文件，则保持选择不变并提示已经在第一个文件。

移动成功后，复用现有 Task Problems 的滚动可见性逻辑，让新选中项保持在可视窗口内。

## 模块边界

- `cr.ui.commands` 解析命令字面量。
- `cr.ui.browser` 负责基于当前可见 Problems 列表移动 `problem_selected` 和 `problem_scroll`。
- `cr.ui.page_content` 和 `cr.ui.command_catalog` 负责中文可发现性文本。
- `cr.ui.task_problems` 继续只负责解析、过滤、排序和格式化，不承担 UI 选择状态。

## 不做

- 不做文件组折叠/展开状态。
- 不做组级选择模型。
- 不做 quick-fix 或外部命令 hook。
- 不做诊断历史、持久化或工具专用 parser。
