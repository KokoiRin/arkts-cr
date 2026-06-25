## 行为

File Detail 页面在主 diff 内容底部预留最多 4 行 review queue dock：

```text
Changed files 2/5  Progress: 1/5 seen
  1 [x] src/A.ets +2 -0
> 2 [ ] src/B.ets +5 -1 note
  3 [ ] src/C.ets +1 -3
```

当空间不足时，优先保留 File Detail 的正文，不强行显示 dock。dock 使用当前 `state.visible_changes`、`state.selected`、`state.seen_paths`、`state.review_notes` 和 `FileChange` 摘要。它是只读提示，不拥有选择状态。

显示窗口以当前文件为中心，最多展示当前文件附近 3 个文件；如果队列更长，用 header 的 `2/5` 表示当前位置和总数，不额外显示省略行，避免挤压 diff。

## 模块边界

- `cr.ui.page_content` 负责 File Detail 页面内容和 dock 文本渲染。
- `cr.ui.browser` 只把当前 `BrowserState` 已有事实传入页面内容，不新增状态源。
- `cr.review.tree` / `cr.vcs.git.FileChange` 继续提供文件摘要事实。
- `cr.ui.workspace` / persistence 不需要变更，因为 dock 复用现有 selected / seen / notes 状态。

## 不做

- 不做点击、鼠标、独立 dock focus。
- 不做可折叠 dock 或 dock 高度设置。
- 不改变 Changed Files 页面树渲染。
- 不改变文件切换、返回、filter 或 review 进度语义。
- 不做 GUI 或 IDE 插件。
