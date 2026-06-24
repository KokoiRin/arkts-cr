## Why

`ReviewWorkspace` 已经拥有 Review Scope、filter、selected file、progress markers 和 review notes 的状态语义，但 `.git/cr/browse-state.json` 的路径、版本校验、JSON 读写、save-on-exit 判断仍在 `src/cr/ui/browser.py`。这让浏览器主模块继续同时承担 session loop、terminal rendering、action execution 和 persistence file I/O。

为了继续朝可扩展 terminal workbench 走，需要把 workspace persistence 深化成独立 UI module。这样后续改存储格式、处理迁移、或换实现语言时，持久化知识集中在一个 seam 上，浏览器只负责在启动和退出时调用它。

## What Changes

- 新增 `cr.ui.workspace_persistence` module，拥有 workspace state path、版本包装/校验、读写、显式 scope 判断和 save-on-exit 规则。
- `browser.py` 保留当前私有 wrapper 名称，委托到新 module，避免本轮大面积重命名。
- 保持 `.git/cr/browse-state.json` 文件路径、schema version、保存内容、恢复条件和容错行为不变。
- 更新架构文档，把 Workspace Persistence 明确为 `cr.ui` 内部 module。

## Capabilities

### New Capabilities

- `browser-workspace-persistence-module`: 定义 browser workspace persistence ownership 和行为保持要求。

### Modified Capabilities

- `browser-workspace-persistence`: persistence file I/O 由新 module 承载，不改变现有恢复体验。
- `review-workspace-module`: `ReviewWorkspace` 继续拥有状态语义，新 persistence module 只负责文件 I/O 和 schema wrapper。

## Impact

- Adds `src/cr/ui/workspace_persistence.py`.
- Touches `src/cr/ui/browser.py` to delegate persistence behavior.
- Updates tests to cover the new module interface while keeping browser compatibility tests.
- Updates CONTEXT, design, navigation roadmap, and P0 notes.
