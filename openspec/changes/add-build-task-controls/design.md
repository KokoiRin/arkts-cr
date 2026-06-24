## Context

`cr browse` 当前只有 `build` 启动命令。build 进程以 `subprocess.Popen` 后台运行，输出被收集到 `BuildState.lines`，底部任务面板显示最近几行和运行结果。已有屏幕布局可以稳定展示后台任务，但任务生命周期还不完整：没有停止、没有重跑，也没有区分用户停止和构建失败。

本轮目标是补齐 build 作为第一个后台任务的最小控制闭环，同时避免过早抽象成通用 task framework。

## Goals / Non-Goals

**Goals:**

- 支持在 interactive browser 中停止正在运行的 build。
- 支持重跑最近一次 build 命令。
- build 面板状态能区分 running、stopping、stopped、succeeded、failed。
- 停止和重跑都不离开当前 review 视图，不影响文件树/diff/commit 导航。
- 保持非 TTY 行模式的 foreground build 行为。

**Non-Goals:**

- 不实现多后台任务队列。
- 不实现独立 task tab、任务历史列表、日志导出。
- 不实现跨平台进程树清理；本轮只终止直接启动的 build 进程。
- 不改变 DouyinHarmony 默认 build 命令或 `--build-cmd` / `CR_BUILD_CMD` 发现规则。

## Decisions

### Decision: 扩展 `BuildState`，不引入通用 Task 抽象

在现有 `BuildState` 上增加 `stop_requested`，用它解释 returncode：如果用户请求停止后进程退出，状态显示为 `stopped`，面板追加 `Build stopped.`；否则按原有成功/失败逻辑处理。

备选方案是新建 `TaskState` / `TaskManager`。它更像 IDE 架构，但当前只有 build 一个后台任务，抽象会比问题本身更大。

### Decision: `stop`/`cancel` 只发送 terminate，不阻塞等待

停止命令对运行中的进程调用 `terminate()`，追加 `Stopping build...`，随后由现有 poll 循环收尾。这样 UI 不会因为等待进程退出而卡住。

备选方案是 stop 命令里直接 `wait()`。它实现简单，但遇到 build 无法立刻退出时会卡住 TUI，违背“主内容继续可用”的目标。

### Decision: `rebuild` 复用当前 build command resolution

`rebuild` / `rerun` 在没有运行中的 build 时重新走 `_start_build(state, args)`。如果 build 正在运行，则不抢占当前任务，只提示先 stop。这样避免隐式杀掉正在运行的 build。

备选方案是 `rebuild` 自动 stop 再 start。它更激进，但容易误杀长时间 build；当前先显式控制。

## Risks / Trade-offs

- [Risk] 某些 build 命令会启动子进程，terminate 直接进程不一定能杀完整进程树。→ Mitigation：本轮记录为 non-goal；后续真实遇到 DouyinHarmony 残留进程时，再设计进程组控制。
- [Risk] stop 后进程可能需要一点时间才退出，期间状态显示 stopping。→ Mitigation：不阻塞 UI，由 poll 循环继续更新。
- [Risk] `rebuild` 名称可能和未来更完整 command palette 冲突。→ Mitigation：同时支持 `rerun`，并把两个命令都限定在 browser command handling 内。
