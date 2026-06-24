## Context

`cr browse` 当前已经是日常入口：默认运行 `cr` 会进入交互式 review browser，并在真实 TTY 中用固定屏幕区域重绘。它解决了“命令行不断刷屏”的主要体验问题，但大 review 里仍然只能线性移动文件，定位目标文件成本较高。

架构上，`src/cr/cli.py` 同时承担参数解析、Git change 选择、review 渲染、browse 状态机、终端 raw key 读取和编辑器打开等职责。这个 module 的 interface 看起来只是 `main()` 和几个 command handler，但 implementation 已经包含多个交互协议。删除测试后可以看到：如果继续把 browse 体验堆在 `cli.py`，过滤、选择、刷新、打开文件这些知识会继续散在 CLI 入口附近，降低 locality。

依赖类型是 in-process 加本地 Git/终端 I/O。过滤和导航状态本身是 in-process，适合收进一个更深的 module；Git 查询和编辑器打开仍然保持现有行为，不新增 adapter 或第三方 TUI 依赖。

## Goals / Non-Goals

**Goals:**

- 在 `cr browse` 的文件列表中支持按路径过滤，让用户可以输入关键字快速缩小 changed-file list。
- 过滤条件对列表模式、文件模式、下一项/上一项、数字选择、刷新后的 selected clamp 都保持一致。
- 在界面中展示当前过滤条件、匹配数量和清除方式。
- 保留非 TTY 行模式，便于测试和不支持 raw key 的终端继续使用。
- 将 browse 相关状态机、渲染、输入解释和打开编辑器逻辑迁入 `src/cr/ui/browser.py`，让 `src/cr/cli.py` 的 browser interface 收敛为一次调用。

**Non-Goals:**

- 不引入 Textual、prompt_toolkit、curses 等第三方 TUI 依赖。
- 不实现鼠标选择、持久化 review session、跨运行保存 seen 状态。
- 不改变 `cr review` / `cr diff` 的输出语义。
- 不重写 Git 数据层或 outline/risk/hunk 的现有实现。

## Decisions

### Decision: 用 `src/cr/ui/browser.py` 承接交互式 browser module

把 `cmd_browse` 背后的状态机、列表/文件渲染、raw key 读取、过滤输入和编辑器打开逻辑移到 `src/cr/ui/browser.py`。`cli.py` 只负责创建 argparse namespace 并调用 `run_browser(args)`。

这样新的 module interface 很小：CLI 调用一个函数，测试可以直接覆盖过滤和渲染 helpers。implementation 内部隐藏终端命令、selected clamp、filter query、mode 切换、refresh 后状态恢复等知识。

备选方案是继续在 `cli.py` 中追加过滤逻辑。它实现最快，但 module 会更浅：调用者和测试都必须知道 browse implementation 的许多细节，后续添加多选、seen、搜索高亮时 locality 更差。

### Decision: 过滤使用大小写不敏感的路径子串匹配

过滤条件匹配完整 Git path，并用 `casefold()` 做大小写不敏感比较。显示时仍然使用现有 `shorten_path()`，避免改变 monorepo 深路径的显示策略。

备选方案是 fuzzy match 或正则。它们更强，但会引入额外语义、转义和排序问题；当前 P0 是“快速缩小列表”，子串匹配足够稳定，也容易测试。

### Decision: `/` 进入过滤输入，`c` / `clear` 清除过滤

在 raw-key TTY 中，用户按 `/` 后临时使用一行 `filter> ` 输入查询；输入结束后下一帧重绘固定区域。非 TTY 行模式支持 `/query` 和 `filter query`，同时支持 `c` / `clear` 清除。空查询等价于清除。

备选方案是在 raw 模式里实现逐字符编辑和实时过滤。这会让终端处理复杂很多，并且需要处理退格、Esc、宽字符等细节；当前先选择稳定的一行输入。

### Decision: 所有导航都基于 filtered view

当 filter active 时，`selected` 始终指向 filtered changes；Enter、数字选择、`n` / `p`、`o` 都操作 filtered view 中的当前文件。刷新后保留 filter query，并把 selected clamp 到新的 filtered view 范围。

备选方案是只过滤列表显示，但文件模式仍用原始 change list。这个 interface 会泄漏“原始列表 vs 可见列表”的内部知识，用户也容易打开看不见的文件。

## Risks / Trade-offs

- [Risk] `c` 作为清除过滤的快捷键未来可能想用于其他命令。→ Mitigation：同时保留 `clear`，并只在 browse command 层处理；如果未来冲突，可以在 OpenSpec 中迁移快捷键。
- [Risk] raw 模式下 `/` 后的一行输入会短暂打印在底部，不是完整实时 TUI 输入框。→ Mitigation：下一帧会重绘固定区域；不引入复杂终端编辑器，先保持可靠。
- [Risk] 从 `cli.py` 移出 browse helpers 会影响现有测试 import。→ Mitigation：测试改为导入 `cr.ui.browser`，CLI 集成测试继续覆盖 `cr` 默认入口。
- [Risk] 新 module 可能复制少量 review helper 知识。→ Mitigation：只移动 browse 所需 helpers，不在本次引入大范围重构；后续若 `review` 和 `browse` 共享规则继续增多，再抽取 change selection module。
