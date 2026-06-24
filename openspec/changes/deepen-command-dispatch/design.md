## Context

`BrowserNavigation` 和 `ReviewWorkspace` 已经分别收拢页面跳转与 review workspace 规则，但 `run_browser` 仍直接拥有大量命令字符串分支。当前代码把三件事混在一起：

- 识别输入字符串和别名。
- 解析参数命令，如 `base REF`、`range OLD..NEW`、`filter QUERY`、数字选择。
- 执行 UI/task/workspace/navigation 行为。

第一阶段只拆第一、二件事。执行逻辑仍留在 `browser.py`，因为它需要 raw-key frame、task lifecycle、workspace、style、args 和状态反馈。

## Goals / Non-Goals

**Goals:**

- 新增 `BrowserCommand` 和 `BrowserCommandAction`。
- 新增 `parse_browser_command(command, raw_keys=...)`，把输入字符串映射到稳定 action。
- 覆盖现有别名、参数命令、数字选择和 unknown fallback。
- 让 `run_browser` 使用 command action，而不是直接散落命令别名集合。
- 保持现有行为和测试。

**Non-Goals:**

- 不新增用户命令。
- 不改变 command palette catalog 或 help 文案。
- 不把所有 action execution 迁入新 module。
- 不改变 raw-key 读取、line-mode 输入、task execution、workspace scope switching 或 navigation 行为。

## Decisions

### Decision 1: 解析 module 不执行动作

`commands.py` 只返回 action 和可选 value。`run_browser` 继续执行动作，因为执行阶段需要访问大量 UI/session 边缘状态。这样能先集中命令语言，同时避免引入一个过大的 dispatcher。

### Decision 2: action 使用稳定字符串常量

使用 `BrowserCommandAction` 常量而不是 enum，保持标准库简单、序列化/测试容易，也与项目现有轻量 class constant 风格一致。

### Decision 3: 参数命令在解析期提取 value

`base REF`、`range OLD..NEW`、`filter QUERY` 和数字选择会在解析期提取参数。执行层不再重复写 `startswith` / `removeprefix`。

## Risks / Trade-offs

- 第一阶段 `run_browser` 仍有较多 action 分支 → 后续可以继续做 action executor，但本轮先避免大重构。
- command palette 的 action 字符串仍与用户命令字符串部分重合 → 解析层会统一处理，保持兼容。
- 过早抽象风险 → 缓解：只抽解析和别名表，测试覆盖现有命令语言，不改变执行行为。
