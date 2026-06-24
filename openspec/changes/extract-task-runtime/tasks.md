## 1. Runtime Module

- [x] 1.1 新增 `src/cr/ui/tasks.py`，包含 Task Panel runtime 职责注释
- [x] 1.2 将 `TaskState`、`TaskRecord`、task label/status/message helpers 移入 runtime module
- [x] 1.3 将 task command resolution 移入 runtime module，并添加直接从 `cr.ui.tasks` 调用的行为测试

## 2. Lifecycle Extraction

- [x] 2.1 将 start、foreground run、failed state、poll、output drain、stop escalation 移入 runtime module
- [x] 2.2 将 stop、rerun、completion history recording 移入 runtime module
- [x] 2.3 保持 `browser.py` 通过 runtime module 调用任务生命周期，Task Panel 渲染仍留在 browser

## 3. Compatibility And Tests

- [x] 3.1 保留 `browser.py` 的兼容 task symbol 导入，降低一次性迁移风险
- [x] 3.2 更新或新增测试，证明 task runtime 权威位于 `cr.ui.tasks`
- [x] 3.3 保持现有 build/test/lint、stop、rerun、history、foreground 行为测试通过

## 4. Documentation

- [x] 4.1 更新 `CONTEXT.md` 的 Task Runtime 术语
- [x] 4.2 更新 `docs/design.md`、`docs/workbench-navigation.md` 和 `docs/p0.md`

## 5. Verification

- [x] 5.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 5.2 Warden 审查确认只迁移 task runtime，不改变 Task Panel 用户行为
