## Context

当前产品层级是 `Review Scope -> Changed Files -> File Detail`。File Detail 内已经有 `next change` / `prev change`，它们把 `state.file_scroll` 移动到已渲染 diff 中的实际 added/deleted 行；也有 `copy line` 复制新文件锚点、`copy hunk` 复制整个 hunk。缺口是定位到某条实际改动行后，不能只复制这一条改动的上下文。

`cr.ui.file_detail_navigation` 已经负责从已渲染 File Detail 文本中识别 hunk header、changed row、当前行新文件行号、active hunk 和 find 结果。`cr.ui.selected_file_actions` 已经负责 selected changed file 上的 copy/open workflow。`BrowserCommandExecutor` 负责页面检查、缓存行获取、状态消息和 redraw。

## Goals / Non-Goals

**Goals:**

- 在 File Detail 中提供 `copy change`。
- 复制当前 `state.file_scroll` 对应的 actual changed row，而不是当前 hunk 或首个改动。
- 对 added 行复制 `path:new_line` anchor，对 deleted 行复制 `old line`，避免伪造新文件位置。
- 保留当前 Review Scope、Changed Files selection、File Detail page/scroll、notes、progress 和 task state。

**Non-Goals:**

- 不新增 `open change`，deleted 行没有稳定的新文件打开位置。
- 不新增真实光标模型或多行选择模型。
- 不改变 `copy line`、`copy hunk`、`next change` / `prev change` 的语义。
- 不持久化当前改动行状态。

## Decisions

1. 当前改动行定义为 `state.file_scroll` 对应的 File Detail body 行，且该行的 diff marker 是 `+` 或 `-`。
   - 理由：现有 File Detail navigation 已经把目标行滚到 `file_scroll`，继续复用这一个位置模型最小。
   - 替代方案：为 File Detail 新增 cursor。暂不采用，因为当前 UI 还没有独立光标，新增状态会让滚动和光标同步变复杂。

2. 改动行解析放在 `file_detail_navigation`。
   - 理由：该模块已经拥有渲染行解析规则，继续集中可以提高局部性；selected-file workflow 不需要了解行号列格式。
   - 替代方案：在 `selected_file_actions` 中解析。暂不采用，因为会让 action workflow 泄漏 File Detail 渲染格式。

3. 复制文本放在 `selected_file_actions` 渲染。
   - 理由：它已经拥有 `copy hunk`、`copy line` 这类 selected file copy workflow，并负责调用 copy 命令。
   - 替代方案：在 browser executor 中拼接文本。暂不采用，因为 executor 应保持页面检查和消息分发角色。

4. deleted 行复制旧行号，不输出 anchor。
   - 理由：deleted 行不存在新文件位置，输出 `path:new_line` 会误导用户；单行 review 片段仍然可以带 `old line` 和原始文本。

## Risks / Trade-offs

- 渲染格式变化可能破坏解析。缓解：解析集中在 `file_detail_navigation`，测试覆盖 added、deleted、context 和 ANSI 颜色。
- 当前行为依赖 viewport 顶部行而非视觉高亮。缓解：现有 jump/find 都以 `file_scroll` 作为当前目标，本轮不引入新 cursor 概念。
- 单行片段上下文较少。缓解：用户仍可用 `copy hunk` 获取更完整上下文。
