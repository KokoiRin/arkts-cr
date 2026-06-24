## 1. Frame Ownership

- [x] 1.1 增加 session-local browser status message
- [x] 1.2 让上下文层渲染 scope + status message
- [x] 1.3 让 raw-key 操作反馈进入状态层而不是直接打印

## 2. Build Panel Safety

- [x] 2.1 build panel 局部刷新拒绝 incomplete/dirty frame
- [x] 2.2 有待渲染状态消息时拒绝 stale partial refresh

## 3. Documentation

- [x] 3.1 更新 `docs/design.md`，明确四层页面模型和渲染所有权
- [x] 3.2 更新 `docs/p0.md`，记录本轮 P0 和下一步方向

## 4. Verification

- [x] 4.1 增加 raw-key open/invalid/unknown command 不旁路 stdout 的测试
- [x] 4.2 增加 dirty frame / pending status 下 build panel 拒绝局部刷新的测试
- [x] 4.3 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
