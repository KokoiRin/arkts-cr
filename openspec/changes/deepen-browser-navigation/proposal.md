## Why

`cr browse` 的产品层级已经明确为 Review Scope、Changed Files、File Detail 和跨层 Command Palette，但页面跳转规则仍散在 `run_browser` 主循环、scope 选择和若干 helper 中。继续往 IDE 替代方向扩展时，如果每个新动作都直接改主循环，导航规则会越来越难验证和迁移。

这次先做一小步架构加深：把现有页面跳转规则收进一个轻量 `BrowserNavigation` module，让浏览器主循环调用意图化接口，而不是直接到处写 `state.page = ...`。

## What Changes

- 新增浏览器导航 module，集中表达现有页面跳转动作。
- 让主浏览器实现通过导航接口进入 Scope Home、Commit Picker、Changed Files、File Detail 和 Command Palette。
- 将常见跳转副作用一起收口：重置 file scroll、list scroll、commit scroll、selected index 或 command/scope selection。
- 保留现有命令、按键、prompt、workspace-state JSON 和用户可见行为。
- 不引入真实 page stack，不新增页面，不拆任务面板，不改变 scope/review 数据加载规则。

## Capabilities

### New Capabilities

- `browser-navigation-module`: 浏览器导航规则由一个 module 拥有，调用方用产品语义动作切换页面，并保持现有行为稳定。

### Modified Capabilities

无。

## Impact

- 主要影响 `src/cr/ui/browser.py`。
- 可能新增 `src/cr/ui/navigation.py`，作为 `cr.ui` 内部 module。
- 需要更新浏览器单元测试、`docs/workbench-navigation.md`、`docs/design.md` 和 `docs/p0.md`。
- 不新增运行时依赖，不改变 CLI 参数或持久化文件格式。
