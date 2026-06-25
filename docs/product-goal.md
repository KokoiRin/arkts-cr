# cr 产品目标

这份文档是 `cr` 的长期目标提示词和产品边界。后续选择 P0、设计功能、判断是否该做 UI，都优先按这里校准。

## 建议 Goal 提示词

我们正在做的不是完整替代 IDE，而是一个面向 AI 编码时代的终端代码工作台：**AI 写代码后的人工接管台 / change workbench**。

目标用户是已经主要让 AI 写代码的人。用户最常见的工作不是从零写代码，而是接管 AI 产物：查看这次改了哪些文件，阅读 diff 和相关源码，做简单跳转，偶尔运行 build/test/lint，查看失败问题和日志，再把最小必要上下文交给 AI 或 reviewer 继续处理。

## Codex 持续执行 Goal

下面这段适合直接作为 Codex Goal 使用。它的重点不是描述愿景，而是约束 Codex 每一轮都能自己选择 P0、实现、验证并提交：

```text
持续推进 /Users/bytedance/Documents/Codex/arkts-cr，把它做成 terminal-first 的 AI change workbench。

产品最终目标：服务“AI 写完代码后，人接管、理解、验证、交还上下文”的 95% 高频流程。核心流程是：
Review Scope -> Changed Files -> File Detail -> Task Output -> Task Problems -> Source File -> Handoff。

每一轮都先阅读 docs/product-goal.md、docs/p0.md、README.md 和当前 git 状态，然后从真实使用摩擦中选择一个最小 P0 垂直切片。P0 只能来自这些方向：
1. 更快查看本轮变更和文件层级。
2. 更顺畅阅读单文件 diff / 源码。
3. 更直接在文件、hunk、改动行、问题、源码之间跳转。
4. 更可靠运行 build/test/lint 并查看 5-10 行任务状态。
5. 更容易从日志和 Problems 定位失败。
6. 更方便复制或保存给 AI / reviewer 的最小上下文。

优先做能减少 IDE、终端、AI 聊天之间来回找上下文的能力。暂时不要做完整 GUI、代码编辑器、语言服务、补全、重构、调试器、大型日志平台或通用任务编排系统。IDE 继续负责编辑；cr 负责变更接管、阅读、验证、导航和 handoff。

每个 P0 必须满足：
- 可以一句话说明它服务哪条核心流程。
- 是一个端到端可用的最小切片，而不是半截基础设施。
- 保持 TUI 简洁，主视图稳定，不重新刷乱用户输入区。
- 核心逻辑尽量沉到 core/domain/helper 层，TUI 只做呈现和输入。
- 不写具体业务仓库特例，仓库命令走配置或已有任务边界。
- 有聚焦测试；风险较高时补回归测试。
- 更新 README 或 docs/p0.md，让产品状态不会漂。

工作方式：
1. 先检查当前实现和未提交改动，不覆盖用户修改。
2. 写或更新一个很小的 OpenSpec/design 记录本轮 P0。
3. 用 TDD 做红绿重构，优先测公开行为。
4. 实现后运行聚焦测试、必要的全量测试、diff check。
5. 用 Warden/自审确认没有越界、过度设计或破坏主流程。
6. 提交并推送，最终用中文汇报：做了什么、为什么是 P0、怎么验证、commit。

如果没有用户新指令，就按 docs/p0.md 的 Next P0 candidates 继续推进；如果发现候选不再是最大摩擦，先更新 docs/p0.md 的判断，再实现新的最小 P0。
```

产品主线应该覆盖这 95% 的日常需求：

```text
AI 改完代码
  -> 查看本轮变更范围
  -> 查看改了哪些文件
  -> 逐文件阅读 diff / 源码
  -> 在文件、hunk、改动行、问题之间快速跳转
  -> 偶尔运行 build/test/lint
  -> 查看任务输出和 Problems
  -> 复制问题 + 源码 + diff 上下文给 AI
  -> 标记已看、写简单备注、继续下一轮
```

`cr` 的首要产品形态仍然是 terminal-first TUI。短期不要急着做完整 GUI，也不要追求替代 IDE 的所有能力。IDE 继续负责编辑、补全、重构、调试；`cr` 负责 AI 代码变更后的理解、验证、导航和 handoff。

长期可以演进为 IDE companion 或独立 UI，但前提是核心工作流和领域模型已经稳定，并且核心能力已经从 TUI 表现层里分离出来。

## 产品一句话

`cr` 是一个终端里的 AI change workbench：帮人接管 AI 写出来的代码，快速看懂变更、验证问题、跳到相关源码，并把关键上下文交还给 AI 或 reviewer。

## 不是要做什么

`cr` 现在不追求：

- 完整替代 JetBrains / VSCode。
- 自己实现语言服务、补全、重构、调试器。
- 做一个大而全 Git GUI。
- 做复杂日志平台。
- 做通用任务编排系统。
- 为了 UI 炫技提前引入 Electron/Tauri/native app 成本。

这些能力将来可能有接口或 companion 形态，但不是当前核心。

## 当前要做什么

当前重点是把这条链路做到顺：

```text
Review Scope -> Changed Files -> File Detail -> Task Problems -> Source File -> Handoff
```

对应能力：

1. 查看变更
   - worktree / staged / all / commit / base / range。
   - 文件层级清楚。
   - staged / unstaged / untracked 可区分。
   - 增删行数、seen/todo、note 清楚。

2. 查看文件
   - 逐文件看 diff。
   - hunk 跳转。
   - 改动行跳转。
   - 当前行 / 当前 hunk / 当前改动可复制。
   - 能打开 IDE 到当前文件或行。

3. 阅读代码
   - 从 Problems 跳到 Source File。
   - 能查找、选择源码范围、复制源码上下文。
   - 不强求完整语言服务，但要有足够好的阅读与 handoff 能力。

4. 简单跳转
   - 文件间 `n/p`。
   - 页面间 `b/forward`。
   - hunk 间 `] / [`。
   - change 间 `next change / prev change`。
   - problem 文件间 `next problem file / prev problem file`。
   - find 结果间 `next match / prev match`。

5. 偶尔运行命令
   - `build` / `test` / `lint`。
   - 底部任务面板不打乱主视图。
   - `task output` 查看完整输出。
   - `stop` / `rerun` 能处理常见场景。

6. 偶尔看日志和问题
   - 先做好 task output 搜索、复制、保存。
   - Problems 页解析 repo-local `path:line[:column]`。
   - 从问题回到源码和 diff。

7. Handoff
   - `copy diff`、`copy hunk`、`copy change`。
   - `copy problem context`。
   - `copy file problems`。
   - `copy prompt` / `save prompt`。
   - 输出应适合直接贴给 AI、PR comment 或同事。

## 理想使用流程

```text
cr
  -> Changed Files
     看本轮文件队列、范围、进度

Enter
  -> File Detail
     看当前文件 diff

] / [ 或 next change
  -> 在文件内跳改动

n / p
  -> 切下一个/上一个文件

build
  -> 底部任务面板运行编译

problems
  -> Task Problems
     看构建问题

view problem
  -> Source File
     看问题附近源码

copy problem context
  -> 把问题 + 源码 + diff 交给 AI
```

## 推荐的近期 P0

P0 必须服务上面的主线。优先级判断：

1. 是否让“AI 改完后人工接管”更快？
2. 是否减少在 IDE / 终端 / AI 聊天之间来回找上下文？
3. 是否让当前文件、当前问题、当前任务输出之间的跳转更直接？
4. 是否能保持 TUI 简洁，不引入太早的 GUI/语言服务复杂度？
5. 是否能沉淀在 core/domain 层，未来换 UI 或换语言也能复用？

近期最值得做的方向：

1. File Detail bottom dock
   - Status: first slice implemented for changed-file queue.
   - 上面看代码，下面保留 changed files / problems 队列。
   - 目标是接近 IDE 的“主编辑区 + 底部变更列表”形态。

2. Build -> Problems -> Source 闭环
   - 编译失败后更快进入问题、跳源码、复制上下文。

3. Source/File Detail 阅读体验
   - Status: first slice implemented for Source File current-symbol hints.
   - 更好的源码范围选择。
   - 当前函数/符号提示。
   - 复制函数块或相关上下文。

4. Task Output 轻量日志能力
   - Status: first slice implemented for copying/saving task output tail.
   - 搜索、复制尾部、保存失败片段。
   - 不做复杂日志平台。

## 关于命令行、IDE 和自有 UI

当前判断：

- 命令行 TUI 仍然有前途，尤其适合远程仓库、大仓库、AI handoff、构建输出和高频键盘操作。
- 现在不要急着做完整自有 GUI。GUI 会带来打包、快捷键、输入法、滚动、主题、跨平台和编辑器集成成本。
- IDE 仍然应该使用。`cr` 不需要替代 IDE 的编辑能力，而是补上 AI 代码接管和上下文整理这块。
- 长期可以做 IDE companion 或自有 UI，但必须先把核心模型从 TUI 表现层里抽干净。

推荐路线：

```text
阶段 1：终端 review workbench
阶段 2：终端 IDE-like layout，比如上方代码、下方文件/问题 dock
阶段 3：IDE companion，和 JetBrains / VSCode 互跳
阶段 4：在 core 稳定后再考虑自有 UI
```

## 架构要求

为了未来可能换 UI、换语言或做 IDE companion，新增能力应尽量遵守：

- core/domain 负责事实和规则：Git change、task output、Problems、handoff、workspace state。
- TUI 只负责呈现、输入和页面状态。
- 外部动作放在边界：open/copy/reveal/build/test/lint。
- 不要把具体仓库特例塞进公共层。
- 不要为了一个低频交互提前引入复杂状态机。
- 每个 P0 都要能说明它服务哪条核心使用流程。

## 选需求时的反问

每次准备实现新功能前，先问：

```text
这个功能是否帮助我更快接管 AI 改动？
它是在增强查看变更、阅读代码、简单跳转、偶尔编译、查看日志这 95% 吗？
它能否保持在 terminal workbench 内完成，而不是提前把我们拖进完整 IDE/GUI？
如果未来做 GUI，这个功能的核心能力能复用吗？
```

如果答案不清楚，就先不要做。
