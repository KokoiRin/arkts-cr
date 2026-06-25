## ADDED Requirements

### Requirement: 页面展示上下文动作条
系统 SHALL 在 raw-key `cr browse` frame 中展示一行与当前页面相关的高频动作提示。

#### Scenario: Changed Files 动作条
- **WHEN** 用户位于 Changed Files 页面
- **THEN** frame SHALL 展示包含打开文件、过滤、标记已看、done-next、任务和命令面板入口的动作条

#### Scenario: File Detail 动作条
- **WHEN** 用户位于 File Detail 页面
- **THEN** frame SHALL 展示包含 hunk/change 导航、查找、打开/复制当前位置、done-next 和返回文件列表的动作条

#### Scenario: Scope Home 动作条
- **WHEN** 用户位于 Scope Home 页面
- **THEN** frame SHALL 展示包含选择 scope、返回、recent commits、base/range 命令和命令面板入口的动作条

#### Scenario: Commit Picker 动作条
- **WHEN** 用户位于 Commit Picker 页面
- **THEN** frame SHALL 展示包含选择 commit、过滤 commit、清除过滤、返回和命令面板入口的动作条

#### Scenario: Command Palette 动作条
- **WHEN** 用户位于 Command Palette 页面
- **THEN** frame SHALL 展示包含执行命令、搜索命令、清除搜索和返回的动作条

### Requirement: 动作条保持 frame 布局稳定
系统 MUST 将上下文动作条作为 main content 的一部分渲染，并保持 prompt 与 Task Panel 区域稳定。

#### Scenario: Task Panel 运行时
- **WHEN** 后台 task 正在运行并触发 raw-key full redraw
- **THEN** frame SHALL 仍保留 Task Panel 区域并在主内容区域内展示动作条

#### Scenario: 终端宽度不足
- **WHEN** 动作条文本超过终端宽度
- **THEN** frame SHALL 截断动作条单行文本而不是让它换行破坏布局

### Requirement: 动作条不改变命令行为
系统 MUST 只展示已有命令提示，不改变命令解析、workspace state 或持久化 schema。

#### Scenario: Existing command parsing
- **WHEN** 用户输入已有命令或快捷键
- **THEN** command parser SHALL 返回与引入动作条之前相同的 BrowserCommandAction

#### Scenario: Workspace persistence
- **WHEN** 浏览器保存 workspace state
- **THEN** persisted data SHALL NOT include contextual action bar state
