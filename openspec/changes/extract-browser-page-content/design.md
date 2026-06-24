## Context

`browser.py` 现在的 interface 太宽：调用方和测试既通过它启动 browser session，也通过它验证 Changed Files、Commit Picker、Scope Home、File Detail 的行渲染。对维护者来说，任何页面主内容变化都混在 raw input、task lifecycle、workspace persistence 和 selected-file side effects 中。

This is an in-process deepening. There is no external adapter and no new runtime dependency. The useful seam is:

```text
Browser orchestration -> Page Content -> rendered main-content lines
```

## Goals / Non-Goals

**Goals:**

- 新增 `cr.ui.page_content`，作为 page-specific main content 的 implementation owner。
- 保留 `browser.py` 里的旧 `_browse_*` wrappers，降低测试和内部调用的一次性迁移成本。
- 保持 `BrowserState` 仍由 browser/workspace/navigation 拥有；Page Content 只读取需要的 state 并返回 lines，必要时回写 scroll offsets。
- 保持 File Detail 的 line cache 由 browser state 承载，不改变缓存 key 或 clear-render-cache 语义。

**Non-Goals:**

- 不重写 `run_browser` 或 raw-key prompt input flow。
- 不改变 Browser Frame / Task Panel 的局部刷新策略。
- 不改变 ReviewWorkspace、Navigation、Command Catalog 或 Task Runtime 的 ownership。
- 不引入 curses、Rich、Textual 或新的 TUI framework。

## Module Interface

`cr.ui.page_content` should expose focused rendering helpers:

- `browse_prompt(page) -> str`
- `browse_help_lines(style) -> list[str]`
- `scope_home_entries() -> tuple[ScopeHomeEntry, ...]`
- `scope_label(state, args) -> str`
- `product_breadcrumb(state, args) -> str`
- `scope_context_line(state, args, style, fit_line) -> str`
- `browse_scope_home_screen_lines(state, style, max_lines) -> list[str]`
- `browse_list_lines(...) -> list[str]`
- `browse_list_screen_lines(state, args, style, max_lines) -> list[str]`
- `browse_commit_lines(...) -> list[str]`
- `browse_commit_screen_lines(state, style, max_lines) -> list[str]`
- `empty_browse_lines(args, filter_text, total_changes, scope_label) -> list[str]`
- `browse_file_lines(...) -> list[str]`
- `file_cache_key(...) -> str`
- `ensure_window(...) -> int`

`browser.py` remains the adapter from live browser session state to these helpers. It may keep wrappers such as `_browse_file_screen_lines` and `_cached_file_lines` so existing tests can still patch browser-level helper names.

## Why This Increases Depth

The new module hides stable knowledge that is currently exposed inside browser orchestration:

- how product breadcrumbs are worded
- how scope home options are rendered
- how Changed Files tree rows are built, styled, selected, and windowed
- how commit picker rows are windowed
- how File Detail headers combine anchors, links, summaries, notes, risks, symbols, purpose, and hunks

Deletion test: if `cr.ui.page_content` were removed, this knowledge would spread back into `browser.py` and tests would again need to reason across session orchestration and rendering details. Keeping it together improves locality for future page-content changes and gives tests a smaller interface for visible page behavior.

## Risks / Trade-offs

- **Risk:** compatibility wrappers mean both old and new names coexist briefly.
  **Mitigation:** wrappers only delegate; implementation lives in `page_content`.

- **Risk:** Page Content needs to read browser state fields, which is not a perfectly narrow typed interface yet.
  **Mitigation:** this is still smaller than moving the full browser renderer; a future typed `PageContentState` can be introduced only if the state interface becomes painful.

- **Risk:** File Detail rendering touches Git facts and source parsing.
  **Mitigation:** keep those calls in the page-content implementation but leave cache storage and invalidation in `BrowserState`, where it already belongs.
