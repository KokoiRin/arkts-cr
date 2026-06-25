## Context

当前 Task Output Page 是 Output Panel：展示当前 task 的状态、命令、输出、搜索和 handoff。Problems 是另一个 IDE 常见视图，但本阶段只做当前 task output 的轻量投影，不建立持久诊断模型。

## Goals / Non-Goals

**Goals:**

- `task problems` / `problems` 从任意页面打开 Task Problems 页。
- 解析当前 task output 中的 repo 内 `path:line[:column]` 锚点。
- 支持相对路径和 repo 内绝对路径。
- Problems 页可选择、滚动、Enter 打开选中问题。
- 没有 task 或没有可识别锚点时显示清晰空状态。

**Non-Goals:**

- 不解析 severity、error code、message category。
- 不为不同构建器写专有 parser。
- 不持久化 diagnostics。
- 不搜索 `TaskRecord` history。
- 不把 problems 混进 Changed Files 或 Review Workspace。

## Decisions

1. **新增 `cr.ui.task_problems`。**
   - 选择：模块输入 repo root 和 task output lines，输出 `TaskProblem` 列表。
   - 理由：解析 task output 是 UI task-view 模型，不属于 Task Runtime 生命周期，也不属于 Git review facts。

2. **Problems 是 BrowserPage。**
   - 选择：新增 `BrowserPage.TASK_PROBLEMS = "problems"`，带独立 `problem_selected` / `problem_scroll`。
   - 理由：它有独立列表、选择和 Enter 行为，属于 IDE panel-style page。

3. **打开动作在 Browser Action Execution 边界完成。**
   - 选择：BrowserCommandExecutor 获取选中 `TaskProblem`，调用 `file_actions.open_path(repo/path, line, open_cmd)`。
   - 理由：编辑器命令是 UI 边缘副作用，已有 file action 模块负责模板和平台 fallback。

4. **先识别通用锚点。**
   - 选择：匹配 `path:line` / `path:line:column`，相对路径必须能定位到 repo 内文件；绝对路径必须在 repo root 下。
   - 理由：覆盖最多工具的基础格式，同时避免误把任意 URL 或日志数字当问题。

## Risks / Trade-offs

- **可能漏掉专有格式**：本 P0 故意不猜具体构建器格式，后续可基于真实日志加 parser。
- **可能有重复锚点**：保留重复出现的日志行，方便用户按日志上下文判断。
- **文件不存在时不显示**：这样能减少误报；但生成文件或删除文件的诊断可能被漏掉，后续再根据真实需求扩展。
