## 1. Build Lifecycle State

- [x] 1.1 扩展 `BuildState`，记录用户请求停止的状态
- [x] 1.2 让 build status 和 poll 收尾逻辑区分 stopped、succeeded、failed

## 2. Browser Commands

- [x] 2.1 增加 `stop` / `cancel` 命令，停止运行中的 build
- [x] 2.2 增加 `rebuild` / `rerun` 命令，在 build 不运行时重跑配置的 build
- [x] 2.3 更新 help、unknown command 文案和 build 面板提示

## 3. Verification And Documentation

- [x] 3.1 增加停止、重跑、运行中防重复启动和状态展示测试
- [x] 3.2 更新 README、`docs/design.md` 和 `docs/p0.md`，记录 build 任务控制能力
- [x] 3.3 运行单元测试、编译检查和 OpenSpec 校验
