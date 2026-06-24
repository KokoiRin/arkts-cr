## Context

当前 browser handoff 的主链路在 `browser.py` 的 `_copy_prompt_handoff`：从 `BrowserState.visible_changes` 选择当前可见 scope 或 selected file，过滤匹配的 review notes，调用 `build_review_data` 和 `render_prompt_handoff`，再交给 `cr.ui.file_actions.copy_text`。这条链路的 Markdown 结构应继续由 `cr.review.prompt` 拥有。

新增保存文件能力时，真正的新行为只有“把同一份 handoff 文本写到一个可预测的位置”。文件路径、目录创建、UTF-8 写入和错误报告适合放在 UI handoff helper，而不是塞进 command parser 或 prompt renderer。

## Goals / Non-Goals

**Goals:**

- `save prompt [PATH]` 保存当前可见 changed files handoff。
- `save prompt file [PATH]` 保存当前选中文件 handoff。
- 默认路径稳定，并自动创建父目录。
- 显式路径可以是 repo-relative 或 absolute。
- 保存失败时返回可读状态消息，不抛出到 browser loop。

**Non-Goals:**

- 不设计 prompt 模板系统。
- 不增加多文件历史归档、时间戳命名或自动打开保存文件。
- 不改变 `copy prompt` 的剪贴板配置、失败文案或空状态行为。
- 不把 prompt Markdown 结构移入 `cr.ui`。

## Decisions

1. **复用一条 handoff 生成 helper**

   将“选哪些 changes、带哪些 notes、构造 review data、渲染 Markdown”收敛成一个内部 helper，供 copy/save 两条输出 adapter 复用。这样保存文件不会复制 prompt 生成规则。

2. **新增轻量 `cr.ui.handoff` 文件输出 helper**

   `cr.ui.handoff` 拥有默认路径、repo-relative/absolute path 解析、父目录创建、UTF-8 写入和错误消息。它不依赖 `BrowserState`，也不渲染 Markdown。

3. **覆盖写入**

   默认 handoff 文件表示“当前 browser review context”，不是审计历史。重复执行覆盖同一路径，避免自动生成多个陈旧文件。后续若需要历史文件，可以作为独立 P0 设计。

## Risks / Trade-offs

- **Risk:** 用户可能希望默认文件名带时间戳。
  **Mitigation:** 先保持可预测路径，方便外部工具、AI 客户端或 shell alias 直接读取。

- **Risk:** 保存路径错误可能污染状态消息。
  **Mitigation:** 写入 helper 捕获 `OSError` 并返回短消息，不改变 page、selection、scope、task state。

- **Risk:** copy/save prompt 两套代码分叉。
  **Mitigation:** 先抽共享 handoff text helper，再接 copy/save 输出。
