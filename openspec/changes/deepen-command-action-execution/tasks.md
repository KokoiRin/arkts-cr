## 1. Action Execution Interface

- [x] 1.1 增加 `BrowserActionResult`，表达 handled、needs_redraw 和 exit_code
- [x] 1.2 增加 `BrowserCommandExecutor`，通过一个 `execute()` 入口执行 parsed command action
- [x] 1.3 增加执行器行为测试，覆盖 redraw、quit 和 unknown fallback

## 2. Browser Loop Integration

- [x] 2.1 让 `run_browser` 在 prompt / palette handoff 之后调用 `BrowserCommandExecutor`
- [x] 2.2 保持 `filter_prompt`、`command_prompt`、raw-key sentinel 和 workspace-save-on-exit 行为不变
- [x] 2.3 保持现有 scope、navigation、task、file open、help 和 unknown command 行为不变

## 3. Documentation

- [x] 3.1 更新 `CONTEXT.md` 的 browser action execution 术语
- [x] 3.2 更新 `docs/design.md`、`docs/workbench-navigation.md` 和 `docs/p0.md`

## 4. Verification

- [x] 4.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 4.2 Warden 审查确认只迁移 action execution，不改变用户命令语义
