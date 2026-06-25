## Context

当前 File Detail 渲染行已经包含 diff hunk header 和 old/new 行号列。`cr.ui.file_detail_navigation` 负责从这些已渲染文本中识别 hunk、查找文本和计算滚动位置；`cr.ui.selected_file_actions` 负责选中文件相关 open/copy 工作流；`BrowserCommandExecutor` 负责页面检查、获取缓存渲染行、展示状态消息。

用户在 File Detail 中通过滚动、`next hunk`、`find TEXT` 或 `next match` 把目标行移动到当前 scroll 后，应该能对这个当前位置执行一个精确行操作。

## Goals / Non-Goals

**Goals:**

- 在 File Detail 中提供 `open line` 和 `copy line` 两个命令。
- 复用已渲染的 File Detail 行号列解析新文件行号。
- 对没有新文件行号的位置给出稳定、可测试的状态消息。
- 保持 `open`、`copy anchor`、`open hunk`、`copy hunk` 现有语义。

**Non-Goals:**

- 不新增光标模型或逐字符选择模型。
- 不改变 `copy anchor` 从文件首个改动行复制锚点的行为。
- 不为 deleted 行猜测旧文件位置或 hunk 起始行。
- 不高亮当前行，不新增鼠标交互。
- 不持久化当前行或行操作状态。

## Decisions

1. 当前行定义为 `state.file_scroll` 对应的 File Detail body 行。
   - 理由：现有 File Detail 导航、hunk 跳转和文本查找都以 `file_scroll` 作为目标位置，复用它最小。
   - 替代方案：新增 cursor 状态。暂不采用，因为会引入第二套位置状态，且当前 UI 还没有真正光标。

2. 新文件行号解析放在 `file_detail_navigation`。
   - 理由：该模块已经负责从渲染 File Detail 文本中提取 hunk、active hunk 和 find 信息；继续把渲染行解析放在这里能保持局部性。
   - 替代方案：在 `selected_file_actions` 里解析文本。暂不采用，因为 selected-file action 不应了解 File Detail 行格式。

3. `open line` / `copy line` 放入 selected-file workflows。
   - 理由：它们和现有 open/copy/hunk action 一样，作用于当前 selected changed file，并复用 editor/copy 配置。

4. deleted 行没有新文件行号时返回空状态。
   - 理由：`open line` 和 `copy line` 目标是当前文件的新文件锚点。deleted 行只属于旧文件，直接复用 hunk 起点会误导用户。

## Risks / Trade-offs

- 渲染格式变化可能影响行号解析。缓解：解析逻辑集中在 `file_detail_navigation`，测试覆盖 hunk header、context、added、deleted 和 ANSI 颜色。
- 当前行是 viewport 顶部而不是真实可视光标。缓解：现有 File Detail 导航都把目标行滚到顶部；命令名先用 `line` 而不引入 cursor 概念。
- metadata 行无法 open/copy。缓解：返回明确消息，避免猜测首个改动行。
