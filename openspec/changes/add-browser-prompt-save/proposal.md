## Why

`copy prompt` / `copy prompt file` 已经能把当前 review handoff 送到剪贴板，但大 review、远程终端、剪贴板命令缺失或需要留档时，用户仍需要把同一份 Markdown 手动重定向成文件。作为 IDE-like workbench，`cr browse` 应该能直接把当前 Review Scope 或当前文件的 handoff 保存为仓内文件。

## What Changes

- 新增 browser 命令 `save prompt [PATH]`，把当前可见 changed files 的 prompt-ready Markdown 写入文件。
- 新增 browser 命令 `save prompt file [PATH]`，把当前选中文件的 prompt-ready Markdown 写入文件。
- 默认保存路径为 `.cr/handoff/review-prompt.md` 和 `.cr/handoff/review-prompt-file.md`；显式 `PATH` 支持 repo-relative 或 absolute 路径。
- 保存逻辑复用 `cr.review.prompt.render_prompt_handoff` 和现有 review notes 过滤规则，不引入 browser 专属 Markdown 格式。
- 更新命令解析、命令目录、README、架构文档和 P0 记录。

## Capabilities

### New Capabilities

- `browser-prompt-save`: Browser 内保存 AI review handoff 文件的命令、路径规则、状态反馈和空状态行为。

### Modified Capabilities

- 无。

## Impact

- 影响 `src/cr/ui/commands.py`、`src/cr/ui/command_catalog.py`、`src/cr/ui/browser.py`，并新增可测试的 handoff 文件输出 helper。
- 不改变 `copy prompt` / `copy prompt file` 的剪贴板行为，不改变 Review Scope / Changed Files / File Detail 层级，不改变 workspace persistence schema。
