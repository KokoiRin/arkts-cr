## Context

`cr browse` 已经有全局帮助、命令面板和页面层级，但高频操作分散在帮助文本和命令列表里。用户进入 Changed Files、File Detail、Scope Home、Commit Picker 或 Command Palette 时，最需要的是“当前页面马上能用的动作”，而不是完整命令字典。

当前渲染分层已经明确：`cr.ui.page_content` 负责页面主内容文本，`cr.ui.frame` 负责屏幕布局和 Task Panel 区域，`cr.ui.browser` 负责组合 frame、页面内容和命令执行。动作条应沿用这条分层。

## Goals / Non-Goals

**Goals:**

- 在 raw-key browser frame 中展示一行页面相关动作提示。
- 每个主要页面显示不同动作集合，帮助用户在当前层级完成高频操作。
- 动作条必须复用已有命令和快捷键，不改变命令语义。
- Task Panel 存在时仍保持固定布局，不让任务输出和动作条互相覆盖。
- 动作条内容由 Page Content 模块持有，方便未来替换 TUI runtime 时迁移。

**Non-Goals:**

- 不做用户自定义快捷键。
- 不新增命令解析 alias。
- 不改变非 raw-key line-mode 的逐次打印行为。
- 不改变 `.git/cr/browse-state.json` schema。
- 不改变 Task Panel 高度算法或后台任务生命周期。

## Decisions

1. **动作条作为 Page Content 纯渲染规则。**
   - 选择：新增 `contextual_action_bar(page, style)` 一类 helper，由 `page_content` 持有每个页面的动作文案。
   - 理由：动作条是页面展示规则，不是命令解析、workspace 状态或 frame 布局。
   - 替代方案：放在 `browser.py` 里直接拼字符串。拒绝，因为会让 browser orchestration 重新承载页面文案知识。

2. **动作条放在 scope/status line 下面、页面主体上面。**
   - 选择：raw-key full redraw 顶部组合为 scope/status line、action bar、page body；完整命令发现继续交给 line-mode 帮助和 Command Palette。
   - 理由：用户先看到自己在哪个 scope，再看到当前可做什么，再进入主体内容。
   - 替代方案：放在 prompt 上方。拒绝，因为 Task Panel 运行时 prompt 上方区域属于任务输出，容易重新制造底部刷新竞争。

3. **每页只保留 5-8 个高频动作。**
   - 选择：动作条是扫描提示，不是完整帮助；完整命令仍由 Command Palette 和 `commands` 承担。
   - 理由：竖屏终端里行数宝贵，动作条过长会降低主内容可读性。
   - 替代方案：展示全部可用命令。拒绝，因为会变成第二个 command list。

4. **动作条不感知复杂运行时状态。**
   - 选择：按页面决定动作，不根据是否有 task、是否有 notes、是否有过滤器动态组合大量变体。
   - 理由：保持实现可预测，避免引入新的状态源；Task Panel 已经显示任务状态，scope/status line 已经显示临时消息。

## Risks / Trade-offs

- **占用一行主内容** → 通过只在 raw-key frame 中展示，并保持单行动作条缓解；任务面板存在时仍由 Browser Frame 计算可用高度。
- **文案过长导致终端换行** → 通过 `fit_terminal_line` 截断整行动作条，保持布局稳定。
- **动作条和全局帮助重复** → raw-key frame 不再常驻整段全局帮助，动作条只放页面高频动作，完整发现能力继续由 line-mode 帮助和 Command Palette 承担。
- **未来命令改名后动作条文案过期** → 测试覆盖关键页面动作文本，命令文档同步更新。
