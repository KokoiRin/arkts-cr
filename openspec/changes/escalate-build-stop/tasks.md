## 1. Stop Escalation State

- [x] 1.1 扩展 `BuildState`，记录 stop 请求时间和是否已强杀
- [x] 1.2 `stop` / `cancel` 设置 stop 请求时间
- [x] 1.3 `_poll_build` 超过宽限期后强杀 build 进程组
- [x] 1.4 确保强杀只触发一次，并保留 stopped 状态语义

## 2. Verification And Documentation

- [x] 2.1 增加 stop 时间记录、超时强杀、只升级一次、无进程组 fallback 测试
- [x] 2.2 更新 README、`docs/design.md` 和 `docs/p0.md`
- [x] 2.3 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
