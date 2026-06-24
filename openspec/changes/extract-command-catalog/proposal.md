## Why

`cr browse` 的命令面已经从一个简单 help list 变成 IDE-like command surface：它有分组目录、可执行命令筛选、命令面板排序、过滤结果计数和屏幕渲染。继续把这些规则留在 `src/cr/ui/browser.py` 会让浏览器主模块同时拥有 session 状态、终端 frame、task panel、action execution 和 command catalog 规则。

为了让后续继续扩展命令面板、快捷键和跨语言迁移更稳，需要把 command catalog/search 深化成独立 UI module。浏览器仍然拥有状态和屏幕调度，但命令目录数据、palette entry 生成、过滤排序和 command help 渲染应集中在一个 module 里。

## What Changes

- 新增 `cr.ui.command_catalog` module，拥有 command catalog 数据结构、目录分组、可执行 palette entry 生成、过滤排序和 command list / command palette 行渲染。
- `src/cr/ui/browser.py` 从该 module 导入接口，保留现有 wrapper 名称以兼容当前测试和内部调用。
- 不改变任何用户可见命令、分组顺序、过滤 ranking、help 文案或 command palette 行为。
- 更新架构文档，把 `Command Catalog` 明确为 `cr.ui` 内部 module。

## Capabilities

### New Capabilities

- `browser-command-catalog-module`: 定义 interactive browser command catalog 的 ownership 和行为保持要求。

### Modified Capabilities

- `browser-command-palette-organization`: command palette organization 由新 module 承载，不改变现有排序。
- `browser-command-dispatch`: command dispatch 仍只解析 typed command，不拥有 catalog 数据或 palette rendering。

## Impact

- Adds `src/cr/ui/command_catalog.py`.
- Touches `src/cr/ui/browser.py` to consume the catalog module.
- Updates tests to cover the new module interface while keeping browser compatibility tests.
- Updates CONTEXT, design, navigation roadmap, and P0 notes.
