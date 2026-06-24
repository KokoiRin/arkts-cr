## Why

`cr browse` 的产品层级已经明确为 `Review Scope -> Changed Files -> File Detail`，但 `src/cr/ui/browser.py` 仍同时拥有 session orchestration、page-specific main content rendering、prompt input flow 和 selected-file action handoff。前几轮已经把 Navigation、ReviewWorkspace、Workspace Persistence、Browser Frame、Command Catalog、Task Runtime、File Actions 和 Prompt Handoff 抽成更深的 UI modules；剩下最大的 in-process 摩擦点是页面主内容的文本生成。

这部分逻辑会继续增长：Changed Files 需要文件树、进度、notes 和过滤；Review Scope 需要 scope home / commit picker；File Detail 需要 diff、purpose、symbols、first-line anchor 和 review note。继续把这些规则留在 browser orchestration 里，会让以后加搜索、诊断、代码动作或更丰富的 handoff 时都绕不开一个大文件。

## What Changes

- 新增 `cr.ui.page_content` module，拥有 browser page main-content 行渲染：help/prompt labels、scope breadcrumbs/context、Scope Home、Changed Files tree/list、Commit Picker、empty state、File Detail lines 和滚动窗口规则。
- `src/cr/ui/browser.py` 保留现有 `_browse_*` helper 名称作为兼容 wrapper，但实现委托给 `cr.ui.page_content`。
- `browser.py` 继续拥有 run loop、raw-key input、screen/frame placement、task panel composition、command execution、workspace startup/exit 和 selected-file action side effects。
- 不改变用户可见页面文案、树形展示、滚动行为、prompt 文案、breadcrumb 文案或缓存语义。

## Capabilities

### New Capabilities

- `browser-page-content-module`: 定义 interactive browser page content 的 ownership 和行为保持要求。

### Modified Capabilities

- `browser-frame`: Browser Frame 仍负责屏幕区域与 Task Panel presentation，但主内容行由 Page Content module 生成。
- `browser-workbench-navigation`: 当前实现映射增加 Page Content module，降低 browser orchestration 对页面文本细节的直接 ownership。

## Impact

- Adds `src/cr/ui/page_content.py`.
- Touches `src/cr/ui/browser.py` to delegate page rendering helpers while preserving compatibility wrappers.
- Updates focused tests to cover the new module interface and keeps browser behavior tests passing.
- Updates CONTEXT, design, navigation roadmap, and P0 notes.
