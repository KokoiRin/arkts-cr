## Why

`cr browse` 的 command palette 已经可以选择并执行命令，但随着 review、scope、build、文件操作、session 操作逐步增加，用户仍然需要在列表里线性扫描。长期目标是替代 IDE 高频操作入口，因此 palette 需要支持快速缩小动作范围。

本轮先做最小可用搜索：在 command palette 中按 `/` 输入过滤词，只显示匹配的命令。这样用户可以输入 `build`、`stage`、`remain`、`open` 等快速定位动作。

## What Changes

- command palette 增加独立 filter 状态。
- raw-key commands mode 下按 `/` 输入 palette filter，而不是改文件路径 filter。
- palette filter 匹配 command label、实际 command、description 和 group。
- raw-key commands mode 下 `c` / `clear` 清 palette filter；离开 commands mode 不影响文件路径 filter。
- 过滤后 selection 和 scroll 自动 clamp 到可见命令。
- 文档说明 command palette 支持 `/` 搜索。

## Capabilities

### New Capabilities
- `browser-command-palette-search`: command palette 内动作搜索/过滤。

### Modified Capabilities
- `browser-command-palette`: 增加独立 filter 状态与匹配渲染。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 `BrowserState`、commands mode 输入处理、palette entries 过滤和渲染。
- 测试需要覆盖 filter 匹配、commands mode `/` 输入、`c` 清除、selection clamp，以及文件 filter 不被污染。
- 不引入 fuzzy search；使用 case-insensitive substring matching。
