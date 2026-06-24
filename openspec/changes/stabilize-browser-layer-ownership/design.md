## 页面层级模型

`cr browse` raw-key 模式采用固定 frame。终端可见区域按从上到下分为四层：

1. 上下文/状态层：当前 scope、筛选、临时操作反馈，例如 opened、invalid choice、unknown command。
2. 主内容层：文件树、commit 列表、单文件 diff、command palette。
3. 后台任务面板层：build 等后台任务的状态、最近日志和最近任务历史。
4. 输入提示层：固定在最后一行的 `cr:list>` / `cr:file>` / `cr:commands>` 等 prompt。

这四层共同构成一个 `BrowserFrame`。raw-key 模式下，除完整 redraw 和受保护的后台任务面板局部刷新外，不允许普通操作直接写 stdout。非 raw line mode 保留现有 `print()` 行为，便于测试、管道和低能力终端使用。

## 渲染所有权

- 完整 redraw 拥有四层：清屏、从第一行重画上下文/主内容/任务面板，并把 cursor 放回输入提示层。
- build 局部刷新只拥有后台任务面板层：它必须在 `BrowserFrame.complete` 为真、布局未变化、且没有待展示状态消息时才允许写终端。
- 临时输入（`:` command prompt、`/` filter prompt）会临时接管输入提示层。返回后必须把 frame 标记为 dirty，让下一次可见更新恢复完整 frame。
- raw-key 操作反馈进入 `BrowserState.status_message`，由上下文/状态层渲染；它不写入 workspace state。

## 最小实现策略

- 在 `BrowserState` 中增加 session-local `status_message`。
- 提供 `_show_browser_message(state, message, raw_keys)`：raw-key 模式写入状态层，line mode 直接打印。
- 让 `_scope_context_line()` 合并 scope 和 status message。
- 将当前 raw-key 可能绕过 frame 的反馈路径改为状态消息：open 成功/失败、无效数字、未知命令、无 recent commits。
- `_draw_build_panel_only()` 在存在状态消息且 frame 未完成重画时拒绝局部刷新，让 run loop 用完整 redraw 收敛页面。

## 风险与取舍

- 这不是最终的 TUI 引擎，只是把当前产品的页面所有权讲清楚并收住 stdout 旁路。
- 状态消息先采用单行显示，后续如果出现多条通知再考虑消息队列。
- `open` 的 subprocess 仍然是边界副作用；本轮只改变用户反馈的呈现位置，不改变打开方式。
