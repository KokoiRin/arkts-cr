## 1. Preset Parsing

- [x] 1.1 增加 `.cr/tasks.json` 读取函数，返回 build/test/lint 字符串 preset
- [x] 1.2 测试缺失文件、无效 JSON、非对象 JSON、非字符串值会被忽略

## 2. Command Resolution

- [x] 2.1 让 `task_command()` 在 CLI 参数和环境变量之后读取项目 preset
- [x] 2.2 保持 DouyinHarmony build 默认作为 build 兜底
- [x] 2.3 测试 CLI > env > preset > DouyinHarmony > missing 的优先级

## 3. Browser Compatibility

- [x] 3.1 保持 `start_task()`、foreground run、raw-key task commands 通过 Task Runtime 自动使用 preset
- [x] 3.2 保持 Task Panel 渲染、task history、stop/rerun 行为不变

## 4. Documentation

- [x] 4.1 更新 `CONTEXT.md` 的 Task Presets 术语
- [x] 4.2 更新 `docs/design.md`、`docs/workbench-navigation.md` 和 `docs/p0.md`
- [x] 4.3 更新 `README.md` 的 `.cr/tasks.json` 使用示例

## 5. Verification

- [x] 5.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 5.2 Warden 审查确认只新增项目任务 preset，不引入复杂 task 平台
