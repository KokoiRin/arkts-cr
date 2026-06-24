## 1. Runtime naming

- [x] 1.1 将 `BuildState` 重命名为 `TaskState`
- [x] 1.2 将 `BrowserState.build` 重命名为 `BrowserState.task`
- [x] 1.3 将 task panel helper 改为 task 命名
- [x] 1.4 将 poll/record/stop/rerun/drain/escalate helper 改为 task 命名
- [x] 1.5 保留 build-specific `_build_command`

## 2. Behavior preservation

- [x] 2.1 更新测试导入和断言到 task 命名
- [x] 2.2 增加命名约束测试，防止主模型退回 `BuildState`
- [x] 2.3 确认 build/test/lint、stop、rerun、面板刷新、行模式行为仍通过

## 3. Documentation

- [x] 3.1 更新 `docs/design.md`
- [x] 3.2 更新 `docs/p0.md` 和 `docs/workbench-navigation.md`

## 4. Verification

- [x] 4.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 4.2 Warden 审查确认这是命名收敛，不是行为扩张
