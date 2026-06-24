## 1. Task History State

- [x] 1.1 增加 `TaskRecord` 和 `BrowserState.task_history`
- [x] 1.2 给 `BuildState` 增加 completion recorded 标记
- [x] 1.3 完成 build 后记录一次 compact task history

## 2. Task Panel Rendering

- [x] 2.1 `_build_panel_lines()` 支持渲染最近 task history
- [x] 2.2 完整 frame 和局部刷新都使用同一 history 渲染
- [x] 2.3 保持面板高度约束和最新日志可见

## 3. Documentation

- [x] 3.1 更新 README，说明底部任务面板显示最近任务结果
- [x] 3.2 更新 `docs/design.md` 和 `docs/p0.md`，记录本轮 P0

## 4. Verification

- [x] 4.1 增加 history 渲染、单次记录和 rerun 保留历史测试
- [x] 4.2 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
