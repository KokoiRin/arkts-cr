## 为什么

`docs/product-goal.md` 把近期 P0 指向了 File Detail bottom dock：用户在读单个文件 diff 时，仍然需要保持对本轮 changed-file 队列的感知。现在 File Detail 是单页沉浸式阅读，想知道还有哪些文件、当前文件在队列里的位置，需要返回 Changed Files。

AI 写代码后的人工接管流程里，读代码和扫文件队列是同一件事的两个视角。一个轻量的底部 review queue 可以让用户在不离开当前 diff 的情况下确认进度、看到相邻文件，并决定下一步 `n/p` 或 `done next`。

## 变更内容

- 在 File Detail 页面内容底部显示 compact changed-files dock。
- dock 展示当前可见 changed-file 队列中当前文件附近的若干项。
- dock 标出当前文件、seen/todo、note、增删行和来源。
- dock 只使用现有 Changed Files / workspace 状态，不新增独立选择或持久状态。
- README、设计文档和 P0 记录更新这条产品能力。

## 影响

- 影响 File Detail 的页面渲染和帮助说明。
- 不改变 `n/p`、`b`、`forward`、`done next`、filter 或 workspace persistence 行为。
- 不做鼠标点击、多 pane focus、可折叠 dock、可配置 dock 高度或 GUI。
