## Context

`cr browse` 当前已经是默认入口，并开始承载文件树、commit review、打开编辑器、build 等常用操作。现有 raw-key 模式通过整屏清空重画主界面，同时 build 运行时用 `_draw_build_panel_only()` 局部刷新底部日志。问题在于 raw-key 读取到普通按键后会额外输出一个换行，输入提示、主内容和 build 面板没有共同的布局契约，导致后台日志更新和用户导航互相影响。

产品定位上，`cr` 不再只是 `git diff` 的漂亮输出，而是一个 terminal workbench：在一个竖屏终端里完成 review、导航、commit 范围切换、build 和后续更多仓库操作。因此本轮优先固定页面层级和刷新边界。

## Goals / Non-Goals

**Goals:**

- 固化 browser 页面层级：帮助/上下文区、主内容区、任务面板区、输入提示区。
- build 面板只能更新自己的任务面板区，不触发主内容滚动，也不覆盖输入提示。
- raw-key 普通按键不产生额外换行；导航后的变化由下一帧重绘表达。
- 让布局计算集中在小的 helper 中，后续增加 test、commit、search、AI action 面板时复用同一边界。
- 更新文档，把当前产品描述为 terminal workbench / lightweight TUI，而不是一次性命令。

**Non-Goals:**

- 不引入第三方 TUI 框架。
- 不做 split pane、多 tab、鼠标、实时命令编辑器。
- 不改变 `cr diff` / `cr review` 的非交互输出。
- 不改变 build 命令发现规则和 DouyinHarmony 默认 build 命令。

## Decisions

### Decision: 引入显式 screen layout helper

新增一个轻量布局对象，统一描述当前终端高度下的四个区域：`content_height`、`build_height`、`prompt_row` 和 `build_start_row`。整屏重画和 build 局部刷新都通过同一个布局计算，避免两个函数各自猜测底部区域在哪里。

备选方案是继续在 `_draw_browse_screen()` 和 `_draw_build_panel_only()` 中各算各的。它改动最小，但这正是现在容易错位的原因：prompt 行、build 起始行、content 截断行缺少共同定义。

### Decision: raw-key 输入不自动换行

raw-key 模式下按键本身只是命令事件，不能向终端输出换行。需要显示用户输入的 filter 或 command 时，再显式进入一行输入 prompt；普通导航、翻页、返回、选择都交给固定区域重绘。

备选方案是在每次命令后立即整屏重画来覆盖换行副作用。它能掩盖一部分问题，但 build 局部刷新和快速按键仍会产生滚动/闪烁，性能和观感都不好。

### Decision: build 面板是底部任务面板，不是日志流

build 输出保留最近 5-10 行，固定显示在主内容下方、输入提示上方。后台 tick 只在面板内容变化时局部刷新这些行，并使用 save/restore cursor 保持输入提示位置。面板存在时，主内容主动让出空间；面板不存在时，主内容占满可用区域。

备选方案是把 build 日志继续 append 到普通 stdout。这对脚本友好，但和交互式 browser 的目标冲突；非 TTY 行模式仍保留 foreground build 输出。

### Decision: 文档记录产品层级而不承诺完整 IDE

README 和设计文档中使用 “terminal workbench / lightweight TUI” 描述当前产品。它的长期目标是替代一部分 IDE 日常操作，但当前明确边界是 review、导航、build 和仓库操作入口，不承诺语言服务、调试器、重构等完整 IDE 能力。

备选方案是直接称为 IDE。这个说法更有野心，但当前能力还没覆盖语言智能和项目管理；用 workbench 更准确，也不会误导后续设计。

## Risks / Trade-offs

- [Risk] ANSI save/restore cursor 在极少数终端表现不同。→ Mitigation：继续保留标准 ANSI 序列，并用测试保证不清屏、不输出换行；Tabby 已能处理 OSC 链接和常见 ANSI。
- [Risk] 不引入成熟 TUI 框架意味着后续复杂交互还要维护自有布局。→ Mitigation：本轮只抽小的布局模型，等页面层级稳定后再评估 prompt_toolkit/Textual 是否值得。
- [Risk] build 输出太快时仍可能频繁刷新底部面板。→ Mitigation：只有面板文本变化才输出，并保留最近行；后续可加刷新节流。
