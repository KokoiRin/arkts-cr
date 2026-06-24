## Why

`cr browse` 已经能在一个会话里切 scope、过滤文件、移动选择和打开 diff。但只要终端关闭或重新启动，用户就会回到默认入口，丢失当前 review 的上下文。这和“替代 IDE 中常用操作”的长期目标不一致：IDE 会记住工作区的大致位置，terminal workbench 也应该记住最基本的 review workspace。

## What Changes

- 默认 `cr browse` 在 clean exit 时保存当前 review workspace。
- 下次默认 `cr browse` 启动时恢复 scope、filter、选中文件和 list/file 层级。
- 状态写入 `.git/cr/browse-state.json`，不污染工作区、不进入 `git status`。
- 用户显式传入 scope 或 pathspec 时，CLI 参数优先，不被历史状态覆盖。
- 不保存 build 任务、diff scroll、缓存、最近 commit drill-in 等临时状态。

## Capabilities

### New Capabilities
- `browser-workspace-persistence`: browser review workspace 的保存与恢复行为。

### Modified Capabilities
- 无。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的启动/退出路径和状态序列化 helper。
- 测试需要覆盖保存、恢复、选中文件恢复、显式 CLI scope 不被覆盖、损坏状态文件容错。
- README、`docs/design.md`、`docs/p0.md` 需要记录这项工作区能力和边界。
