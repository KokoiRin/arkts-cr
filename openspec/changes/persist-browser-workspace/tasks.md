## 1. Workspace State Persistence

- [x] 1.1 增加 browser workspace 状态文件路径、读写和容错 helper
- [x] 1.2 clean exit 时保存 scope、filter、selected path/index 和 list/file mode
- [x] 1.3 默认 `cr browse` 启动时恢复保存的 scope、filter 和选中文件
- [x] 1.4 显式 scope 或 pathspec 参数出现时跳过恢复
- [x] 1.5 损坏或不兼容状态文件不影响 browser 启动

## 2. Verification And Documentation

- [x] 2.1 增加保存、恢复、CLI override、损坏状态容错测试
- [x] 2.2 更新 README、`docs/design.md` 和 `docs/p0.md`
- [x] 2.3 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
