## Context

目前 `find TEXT` / `next match` / `prev match` 只在 File Detail 中工作。Task Output Page 已经是一个独立 browser page，有自己的 `task_scroll`，但没有文本定位能力。直接调用 `file_detail_navigation.find_text` 可以工作，却会让 Task Output 依赖 File Detail 模块，违反现有职责边界。

## Goals / Non-Goals

**Goals:**

- Task Output Page 中 `find TEXT` 跳到当前任务输出首个匹配行。
- `next match` / `prev match` 在 Task Output Page 中复用最近一次 task output query 循环跳转。
- File Detail 现有查找行为保持不变。
- 通用 rendered-text search 不知道 BrowserState、TaskState、Git diff 或页面类型。

**Non-Goals:**

- 不解析错误格式或 warning。
- 不新增 Problems/Diagnostics 页。
- 不打开匹配行对应文件。
- 不搜索 TaskRecord history。
- 不持久化 task find query 或 task scroll。

## Decisions

1. **新增 `cr.ui.text_search` 作为纯 helper。**
   - 选择：模块提供 `find_text(lines, query, skip_first_line=True)` 和 `find_next_text(...)`。
   - 理由：File Detail 和 Task Output 都是在“已渲染行”里查找文本；通用逻辑应脱离 File Detail 名词。

2. **Task Output 使用独立 `task_find_text`。**
   - 选择：`BrowserState` 增加 `task_find_text`，只在 Task Output Page 的 find 中读写。
   - 理由：File Detail 和 Task Output 是不同页面，互相复用搜索词会造成用户困惑。

3. **保持现有命令名。**
   - 选择：继续使用 `find TEXT`、`next match`、`prev match`，根据当前页面分发。
   - 理由：用户不需要学习 `find task` 这种新命令；它和 IDE 当前面板搜索一致。

## Risks / Trade-offs

- **新增模块可能显得小**：但它明确消除了 Task Output 对 File Detail navigation 的概念依赖，并为后续 Command Palette/Problems 等 rendered text 搜索留出干净落点。
- **没有高亮匹配**：先实现定位和重复跳转，避免把渲染样式复杂度带入本 P0。
- **任务输出运行中变化**：重复跳转基于调用时刻的当前 captured lines；如果输出新增，下一次查找自然看到新内容。
