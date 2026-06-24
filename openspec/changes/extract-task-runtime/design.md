## Context

当前 Task Panel 已经具备较多 runtime 行为：命令解析、后台进程启动、非阻塞 stdout 采集、停止进程组、停止升级强杀、前台运行、重跑最近任务、完成历史记录，以及 build/test/lint 的配置规则。它们仍位于 `src/cr/ui/browser.py`，而 `browser.py` 同时还负责浏览器页面、命令执行、渲染、编辑器打开和 workspace persistence。

按架构术语看，这个候选属于 local-substitutable / true external 混合：核心状态和历史记录是 in-process；进程启动与信号是本地 OS 边缘，可以用短命令、fake process、mock `os.killpg` 验证。它适合先做 internal seam，不需要对外暴露复杂 port。

## Goals / Non-Goals

**Goals:**

- 新增 `src/cr/ui/tasks.py`，作为 Task Panel 背后的 runtime module。
- 将 `TaskState`、`TaskRecord`、任务命令解析、后台启动、前台运行、轮询、输出 drain、停止、升级强杀、重跑、历史记录移动到 task runtime module。
- 让 `browser.py` 只调用 task runtime interface，并继续负责 task panel 渲染、Browser Frame 布局和用户反馈区域。
- 保持 build/test/lint 命令、环境变量、DouyinHarmony 默认 build、停止语义、历史记录和测试行为不变。

**Non-Goals:**

- 不新增 task kind。
- 不实现多个并发 task。
- 不实现 task preset 文件或项目配置文件。
- 不改变 bottom panel 的显示布局。
- 不改变 raw-key / line-mode 的任务交互。

## Decisions

### 1. `cr.ui.tasks` 是 runtime module，不是渲染 module

选择：把生命周期、状态和命令解析移动到 `tasks.py`，但 `_task_panel_lines`、`_task_status` 这类渲染函数暂留 `browser.py`，或只依赖 task runtime 提供的状态/label helper。

原因：Task Panel 渲染依赖 TerminalStyle、屏幕高度、BrowserFrame 和当前 UI 布局；过早移动会让 `tasks.py` 反向知道 browser frame 细节，module interface 变浅。

替代方案：把 Task Panel 渲染也一起移动。暂不采用，因为这会混合 runtime 和 screen rendering layer。

### 2. 保持 BrowserState 挂载当前 task 和 history

选择：`BrowserState.task` 和 `BrowserState.task_history` 继续存在，但它们的类型来自 `cr.ui.tasks`。

原因：BrowserState 是 UI session state，当前任务和最近历史仍属于 session；runtime module 不需要拥有整个 BrowserState。这样 `tasks.py` 只处理 `TaskState` / `TaskRecord` 数据，避免依赖 browser session。

替代方案：新增 `TaskRuntimeState` 并嵌入 BrowserState。暂不采用，本轮目标是迁移现有 runtime，不引入双状态源。

### 3. 保留兼容导入一轮

选择：`browser.py` 从 `tasks.py` import 后继续 re-export 当前测试和外部代码可能引用的 task symbols，例如 `TaskState`、`start_task` 的 `_start_task` 兼容名。

原因：当前测试集中有大量历史 import。一次性全部改名会让 diff 噪声盖过真实迁移。新测试应优先 import `cr.ui.tasks`，旧兼容名后续可以分阶段删除。

替代方案：立刻删除 `browser.py` 的私有 helper 兼容名。暂不采用，因为这会把行为迁移和测试清理混成一刀。

## Risks / Trade-offs

- [Risk] 只移动代码但 interface 仍然很薄。→ Mitigation：`tasks.py` 顶部职责注释明确 runtime ownership，并让测试从 `cr.ui.tasks` 验证命令解析、启动、停止、轮询和历史。
- [Risk] 进程/信号行为在迁移中细微变化。→ Mitigation：复用现有实现，跑完整任务相关测试和全量测试。
- [Risk] 兼容 re-export 让 browser 仍看起来拥有 task helper。→ Mitigation：文档标注 `cr.ui.tasks` 为权威 runtime，P0 后续可做测试 import 清理。
