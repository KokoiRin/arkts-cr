## Context

当前 File Detail 的细粒度导航已经集中在 `cr.ui.file_detail_navigation`：hunk header 发现、active hunk、文本 find、重复 find、当前行新文件行号解析都从已渲染的 File Detail 行中提取信息。`BrowserCommandExecutor` 负责 File Detail 页面检查、获取缓存渲染行、应用 scroll 和状态消息。

`next change` / `prev change` 继续沿用这条接缝：核心规则在 `file_detail_navigation`，执行器只应用结果。

## Goals / Non-Goals

**Goals:**

- 在 File Detail 中提供 `next change` 和 `prev change`。
- 只跳到实际 changed rows：added 行和 deleted 行。
- 支持从当前 `file_scroll` 向前/向后查找并在文件内 wraparound。
- 没有 changed rows 时保持当前 scroll 并报告空状态。
- 保持 Review Scope、selected file、filters、notes、progress、task state、page 不变。

**Non-Goals:**

- 不把 context 行、hunk header 或 metadata 行视为 changed rows。
- 不新增 cursor 状态；当前行仍由 `file_scroll` 表示。
- 不改变 diff 渲染格式。
- 不改变 `n` / `p`、hunk navigation 或 match navigation。
- 不持久化 changed-line navigation 状态。

## Decisions

1. changed row 识别放在 `file_detail_navigation`。
   - 理由：它已经是 File Detail 渲染文本导航规则的深模块，新增判断不会泄漏到 browser orchestration。
   - 替代方案：在 `browser.py` 里扫描字符串。拒绝，因为会让大型 orchestration 模块继续吸收规则。

2. 命令名使用 `next change` / `prev change`。
   - 理由：不占用 `n` / `p`，和 `next hunk`、`next match` 形成同一命令族。
   - 替代方案：使用 `]c` / `[c`。暂不采用，因为当前 raw-key parser 已经把 `]` / `[` 用给 hunk，复合键会加大输入协议复杂度。

3. wraparound，而不是停在边界。
   - 理由：这和 repeated find 的体验一致，适合在一个文件内快速循环检查所有 changed rows。

## Risks / Trade-offs

- 渲染行格式变化可能影响 changed row 识别。缓解：集中解析并用 ANSI、added、deleted、context、metadata 测试覆盖。
- 当前行仍是 viewport 顶部。缓解：与现有 hunk/find/current-line action 模型保持一致，不提前引入 cursor。
- `change` 一词也可表示文件变更。缓解：命令只在 File Detail 内跳转，文档明确为 added/deleted rows。
