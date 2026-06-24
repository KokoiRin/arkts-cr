## 1. Build Process Group Lifecycle

- [x] 1.1 扩展 `BuildState`，记录后台 build 的进程组 id
- [x] 1.2 后台 build 启动时创建独立进程组
- [x] 1.3 `stop` / `cancel` 优先终止整个进程组
- [x] 1.4 进程组终止失败时 fallback 到父进程终止，并写入 build 面板

## 2. Verification And Documentation

- [x] 2.1 增加覆盖进程组启动、停止子进程、fallback 文案的测试
- [x] 2.2 更新 README、`docs/design.md` 和 `docs/p0.md`
- [x] 2.3 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
