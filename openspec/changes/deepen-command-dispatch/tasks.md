## 1. Command Dispatch Module

- [x] 1.1 增加 `BrowserCommandAction` 和 `BrowserCommand`
- [x] 1.2 增加 `parse_browser_command()`，覆盖现有命令别名、参数命令、数字选择和 unknown fallback
- [x] 1.3 增加命令解析行为测试

## 2. Browser Integration

- [x] 2.1 让 `run_browser` 使用 parsed command action 执行现有行为
- [x] 2.2 保持 command prompt、filter prompt、palette enter handoff 和 raw-key sentinels 行为不变
- [x] 2.3 保持 command palette catalog 和 help 文案不变

## 3. Documentation

- [x] 3.1 更新 `CONTEXT.md`
- [x] 3.2 更新 `docs/design.md`、`docs/workbench-navigation.md` 和 `docs/p0.md`

## 4. Verification

- [x] 4.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 4.2 Warden 审查确认只迁移命令解析，不改变执行语义或用户命令
