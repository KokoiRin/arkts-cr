## Why

`cr browse` 已经支持给单个 changed file 写轻量 review note，但用户只能在 Changed Files 的紧凑标记和 File Detail 里逐个查看。一次 review 里 notes 往往是“稍后统一处理”的线索，所以需要一个低成本汇总入口，让用户在不离开当前 review 工作流的情况下看到所有备注。

## What Changes

- 新增 `notes` 浏览器命令，汇总当前 workspace 中已有的 review notes。
- 汇总列表优先按当前 changed files 的 review 顺序展示；不在当前变更列表里的持久化 notes 追加在末尾并按路径排序。
- 没有 notes 时展示明确空状态。
- 将 `notes` 加入命令目录和命令面板。

## Capabilities

### New Capabilities

- `browser-review-notes-summary`: 定义 interactive browser 的 review notes 汇总能力。

### Modified Capabilities

- `browser-review-notes`: 在 set/clear/display/persist 的基础上增加可扫视的汇总入口。

## Impact

- Touches `src/cr/ui/commands.py` for `notes` command parsing.
- Touches `src/cr/ui/browser.py` for summary rendering and command catalog.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
- Adds focused tests for command parsing, summary ordering, command execution, and command catalog discoverability.
