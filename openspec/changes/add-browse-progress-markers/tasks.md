## 1. Browser Progress State

- [x] 1.1 扩展 `BrowserState`，记录 seen paths 和 remaining-only 开关
- [x] 1.2 将 remaining-only 过滤接入 `visible_changes`
- [x] 1.3 将 seen paths 和 remaining-only 写入/恢复 browser workspace state

## 2. Commands And Rendering

- [x] 2.1 增加 mark seen / unmark / remaining / allfiles 命令
- [x] 2.2 在文件列表和文件 diff 中展示 progress/seen 状态
- [x] 2.3 更新 command list 和 unknown-command 文案

## 3. Verification And Documentation

- [x] 3.1 增加 mark/unmark、remaining、持久化恢复、渲染测试
- [x] 3.2 更新 README、`docs/design.md` 和 `docs/p0.md`
- [x] 3.3 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
