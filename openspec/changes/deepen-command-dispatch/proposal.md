## Why

`cr browse` 的 `run_browser` 主循环仍然直接识别大量命令字符串，例如 `build`、`scope`、`back`、`remaining`、`base REF` 和数字选择。随着 terminal workbench 的动作越来越多，继续把字符串识别和动作执行混在同一个循环里，会让命令扩展、测试和未来迁移语言都变得更脆。

本轮做第一阶段 command dispatch deepening：新增命令解析 module，把输入字符串转成产品动作，主循环只根据动作执行现有行为。

## What Changes

- 新增 browser command dispatch module。
- 将命令字符串、别名和带参数命令解析成 `BrowserCommand` / `BrowserCommandAction`。
- 让 `run_browser` 先解析命令，再按 action 执行现有行为。
- 保持所有用户命令、快捷键、prompt、command palette 和 unknown-command 文案不变。
- 不迁移 task/workspace/navigation 的执行逻辑，不新增命令，不改变 raw-key 读取协议。

## Capabilities

### New Capabilities

- `browser-command-dispatch`: 浏览器命令输入由 dedicated module 解析成产品动作，UI 主循环不直接拥有命令字符串别名表。

### Modified Capabilities

无。

## Impact

- 主要影响 `src/cr/ui/browser.py`。
- 可能新增 `src/cr/ui/commands.py`，作为 `cr.ui` 内部 module。
- 需要增加命令解析测试，并保持现有 browser 行为测试通过。
- 不新增运行时依赖，不改变 CLI 参数或用户可见行为。
