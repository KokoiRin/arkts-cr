## 1. Review Workspace Module

- [x] 1.1 增加 `ReviewWorkspace` module、`ReviewScope` 和默认 changed-file loader
- [x] 1.2 让 workspace 暴露 visible changes、filter/progress、selection 和 scope capture 行为
- [x] 1.3 将 commit 选择、scope 切换和 previous scope restore 的核心规则迁入 workspace

## 2. Browser Integration

- [x] 2.1 让 `BrowserState` 持有/委托 `ReviewWorkspace`，保持现有属性兼容
- [x] 2.2 将 `_select_commit`、`_switch_review_scope`、`_restore_previous_scope` 改为调用 workspace 行为
- [x] 2.3 保持 workspace state JSON 字段和值不变

## 3. Tests And Documentation

- [x] 3.1 增加 `ReviewWorkspace` 行为测试
- [x] 3.2 保持现有 browser scope、commit、persistence 测试通过
- [x] 3.3 更新 `CONTEXT.md`、`docs/design.md`、`docs/workbench-navigation.md` 和 `docs/p0.md`

## 4. Verification

- [x] 4.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 4.2 Warden 审查确认没有迁入 UI-only 状态、没有改变 persistence 格式、没有做大重构
