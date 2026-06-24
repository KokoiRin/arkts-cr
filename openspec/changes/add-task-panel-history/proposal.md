## Why

`cr browse` 的底部任务面板现在只显示当前 build 的最近日志和状态。对于一个想替代 IDE 高频操作的小工具来说，用户需要知道刚刚跑过的任务结果：上一次 build 是成功、失败还是被停止；重跑后也不应该完全丢失前一次结果。

本轮先做最小任务历史：记录最近完成的 build 任务，并在底部任务面板中展示一行 compact history。这样后续增加 test/lint 或多任务时，可以沿着同一个任务面板模型扩展，而不是继续把日志当 stdout。

## What Changes

- 增加轻量任务历史记录，保存最近 build 的命令、最终状态和返回码。
- build 完成、停止或失败后，将结果加入 browser session 的 task history。
- build 面板在当前任务状态下方展示最近任务结果摘要。
- 历史只保留当前 browser session，不写入 workspace state。
- 不引入多任务并发，也不新增 test/lint 命令。

## Capabilities

### New Capabilities
- `browser-task-panel-history`: browser 底部任务面板的最近任务结果记录。

### Modified Capabilities
- `browser-screen-layout`: build 面板继续使用同一底部任务区域，但内容包含 compact history。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 build polling、build panel rendering 和 browser session state。
- 测试需要覆盖 history 渲染、完成时只记录一次、rerun 后保留前一次任务结果。
- 不改变 foreground line-mode build 输出。
