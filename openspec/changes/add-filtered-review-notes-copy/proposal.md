## Why

`notes QUERY` 可以筛选 review notes，`copy notes` 可以复制完整 notes 汇总。实际使用时，用户经常会先筛出某类备注，再把这组结果贴到聊天、AI prompt 或 PR comment。现在需要手动复制终端输出，工作流断了一步。

## What Changes

- 新增 `copy notes QUERY`，复制与 `notes QUERY` 相同的过滤结果。
- `copy notes` / `notes copy` 保持复制完整 notes 汇总。
- 没有匹配结果时显示明确提示，不调用剪贴板命令。
- 复制继续复用 `--copy-cmd` / `CR_COPY_CMD`，不新增配置。

## Capabilities

### Modified Capabilities

- `browser-review-notes-copy`: 支持复制完整或过滤后的 review notes summary。
- `browser-review-notes-search`: `copy notes QUERY` 复用同一套路径/备注文本匹配规则。

## Impact

- Touches `src/cr/ui/commands.py` for `copy notes QUERY` command parsing.
- Touches `src/cr/ui/browser.py` for filtered copy execution and command catalog help.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
- Adds focused tests for parsing, filtered copy success, no-match state, raw-key feedback, and command list discoverability.
