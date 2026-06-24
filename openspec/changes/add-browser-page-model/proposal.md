## 为什么

`cr browse` 的产品层级已经明确为 `Review Scope -> Changed Files -> File Detail`，旁边还有 `Command Palette` 和 `Task Panel`。但代码主循环仍然使用裸字符串 `mode="list"`、`mode="file"`、`mode="commits"`、`mode="commands"`、`mode="scopes"` 表达页面状态。

这些字符串短期能跑，但长期会让页面层级、scope 选择器、文件列表和命令面板混在一起。后续如果要拆 `BrowserNavigation`、引入页面栈、或者迁移语言，最好先让页面命名成为一个显式模型。

## 改什么

- 新增 `BrowserPage` 页面命名模型。
- 将 `BrowserState` 的主字段从 `mode` 收敛到 `page`。
- 保留短期 `mode` 兼容属性，让已有测试和少量调用点可以逐步迁移。
- 用产品语义命名页面：
  - `SCOPE_HOME`
  - `COMMIT_PICKER`
  - `CHANGED_FILES`
  - `FILE_DETAIL`
  - `COMMAND_PALETTE`
- 让渲染、提示符、breadcrumb、选择移动等主链路使用 `BrowserPage` 常量，而不是散落裸字符串。

## 不做

- 不实现真正的 page stack。
- 不新增用户命令或页面。
- 不改变 `cr:list>` / `cr:file>` / `cr:commits>` 等现有提示符。
- 不改变 workspace persistence 的外部 JSON 值。
- 不拆分 `src/cr/ui/browser.py` 到新模块。
