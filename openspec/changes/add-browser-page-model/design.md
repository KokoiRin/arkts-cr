## 设计

当前浏览器仍然由 `src/cr/ui/browser.py` 拥有。为了避免把命名收敛升级成大重构，本轮只在同一模块中增加轻量页面模型。

## 页面模型

新增 `BrowserPage`，用产品语义命名现有页面：

```text
SCOPE_HOME      -> "scopes"
COMMIT_PICKER   -> "commits"
CHANGED_FILES   -> "list"
FILE_DETAIL     -> "file"
COMMAND_PALETTE -> "commands"
```

字符串值暂时保持不变，因为它们已经出现在 prompt、workspace-state JSON、行模式测试和用户认知里。新的价值在于：主代码读到的是页面概念，不是偶然字符串。

## 状态字段

`BrowserState.page` 成为主字段。短期保留 `mode` property：

- 读 `state.mode` 返回 `state.page`。
- 写 `state.mode = ...` 会写入 `state.page`。

这样现有测试和少量外部调用不必一次性全部迁移，但主实现可以逐步以 `page` 为准。

## 行为保持

- 所有键盘和命令行为保持不变。
- prompt 文案保持不变。
- workspace-state JSON 的 `mode` 字段保持不变。
- `b` / left / Enter / Home / End / page navigation 行为保持不变。

## 测试策略

- 增加模型测试：`BrowserPage` 包含所有现有页面，`BrowserState.page` 默认是 Changed Files，`mode` 兼容属性读写同一个状态。
- 增加约束测试：browser 主实现包含 `BrowserPage.CHANGED_FILES` 等产品语义常量。
- 保留现有行为测试覆盖实际交互。
