## 1. Page model

- [x] 1.1 增加 `BrowserPage` 页面命名模型
- [x] 1.2 将 `BrowserState` 主字段改为 `page`
- [x] 1.3 保留 `mode` 兼容 property
- [x] 1.4 让主实现使用 `BrowserPage` 常量

## 2. Behavior preservation

- [x] 2.1 增加 page model 和兼容属性测试
- [x] 2.2 确认 prompt 和 workspace persistence 的旧值不变
- [x] 2.3 确认 scope home、commit picker、changed files、file detail、command palette 导航行为不变

## 3. Documentation

- [x] 3.1 更新 `docs/workbench-navigation.md`
- [x] 3.2 更新 `docs/p0.md` 和 `docs/design.md`

## 4. Verification

- [x] 4.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 4.2 Warden 审查确认没有引入真正 page stack 或行为扩张
