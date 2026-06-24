## Why

`cr browse` 已经支持给文件写 review note，并用 `notes` 汇总当前 workspace 的备注。下一步的真实使用摩擦是：这些备注经常要被带到聊天、AI prompt、PR comment 或临时文档里继续处理。如果只能在终端里看，notes 仍然像一个封闭面板，而不是 review 工作流里的可携带上下文。

## What Changes

- 新增 `copy notes` 命令，复制当前 `notes` 汇总到剪贴板。
- 支持别名 `notes copy`，贴合用户从 notes 工作流出发的输入习惯。
- 没有备注时显示明确空状态，不调用剪贴板命令。
- 复制内容复用 `notes` 的排序与格式，避免出现两套 review note 表达。

## Capabilities

### New Capabilities

- `browser-review-notes-copy`: 定义 interactive browser 中复制 review notes 汇总的能力。

### Modified Capabilities

- `browser-review-notes-summary`: 复制内容复用现有 notes summary。
- `browser-file-actions`: 复制 notes 使用现有 clipboard command resolution，不新增剪贴板配置。

## Impact

- Touches `src/cr/ui/commands.py` for `copy notes` / `notes copy` command parsing.
- Touches `src/cr/ui/browser.py` for command execution and command catalog visibility.
- Reuses `cr.ui.file_actions.copy_text` and existing `--copy-cmd` / `CR_COPY_CMD`.
- Updates README, CONTEXT, design, navigation roadmap, and P0 notes.
- Adds focused tests for parsing, execution, empty state, raw-key feedback, and command catalog discoverability.
