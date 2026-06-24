## Context

`src/cr/ui/browser.py` 当前同时拥有 browse session state、渲染、命令读取、命令分发、scope 切换、页面跳转、任务面板和编辑器打开。上一轮已经引入 `BrowserPage` 和 `BrowserState.page`，让页面名称显式化；下一步应把“怎么从一个页面跳到另一个页面”的规则集中起来。

这属于 in-process deepening：没有 I/O、没有外部 adapter、没有部署 seam。收益来自 locality：修改 back/enter/next/palette/scope-home 规则时，不需要在主循环和多个 helper 中寻找散落的状态重置。

## Goals / Non-Goals

**Goals:**

- 新增一个轻量 `BrowserNavigation` module 或等价内部 module。
- 用小 interface 表达现有导航意图，例如进入 Changed Files、File Detail、Command Palette、Scope Home、Commit Picker，以及返回上一层。
- 将页面跳转常见副作用收口到该 module：scroll reset、selection reset、page assignment。
- 保持所有现有用户行为和兼容字段不变。
- 让测试能直接验证导航规则，而不是只通过完整 browse loop 间接覆盖。

**Non-Goals:**

- 不实现真实 page stack、历史记录或 forward/back 栈。
- 不新增用户命令、快捷键、页面或 scope 类型。
- 不改变 build/test/lint Task Panel。
- 不改变 workspace-state JSON 的 `mode` 字段和值。
- 不把整个 `browser.py` 拆成多个大文件。

## Decisions

### Decision 1: 新 module 只拥有导航，不拥有数据加载

`BrowserNavigation` 只修改 `BrowserState` 的页面、选择和滚动字段，不调用 Git、不加载 commits、不切换 review scope。scope 切换和 commit 选择仍留在现有 helper 中，因为它们涉及 `argparse.Namespace` 和 Git 数据加载。

替代方案是把 `_select_commit`、`_switch_review_scope` 也塞进 navigation module。暂不采用，因为那会把导航 module 变成 review workspace module，一步太大。

### Decision 2: interface 使用动作名，不暴露 raw page 字符串

调用方应写 `navigation.show_changed_files(state)`、`navigation.open_file_detail(state)`、`navigation.go_back(state)` 这类动作，而不是继续散写 `state.page = BrowserPage.FILE_DETAIL`。这让主循环读起来像产品行为，也给后续真实 page stack 留位置。

### Decision 3: 保留 `BrowserPage` 字符串值和 `BrowserState.mode`

`BrowserPage` 的值继续是 `"scopes" / "commits" / "list" / "file" / "commands"`。`mode` 继续作为兼容属性存在，workspace persistence 仍保存旧 `mode` 字段。本轮是内部结构加深，不做迁移。

### Decision 4: 测试 focus 在导航 module interface

新增测试应覆盖导航 interface 的可观察结果：页面、scroll、selection 变化和 back 行为。现有完整 browser loop 测试继续证明用户行为没有变。

## Risks / Trade-offs

- 新 module 如果只是一层薄转发，会变成浅 module → 缓解：把页面赋值和相关 reset 规则一起收进去，让它隐藏调用顺序。
- 真实 page stack 还没实现，`go_back` 仍是当前层级规则 → 缓解：文档明确这是当前层级返回，不伪装成历史栈。
- `browser.py` 仍然很大 → 缓解：本轮只收导航规则，后续再考虑 ReviewWorkspace 或渲染/命令分发拆分。
