## 1. Navigation Module

- [x] 1.1 增加 `BrowserNavigation` module 和页面跳转接口
- [x] 1.2 将主 browse loop 的常见页面跳转改为调用导航接口
- [x] 1.3 将 scope home / commit picker helper 中的页面跳转接入导航接口

## 2. Behavior Preservation

- [x] 2.1 增加导航 module 行为测试
- [x] 2.2 确认 back、open file、next/previous、scope home、commit picker 和 command palette 行为不变
- [x] 2.3 确认 workspace persistence 的 `mode` 字段和值不变

## 3. Documentation

- [x] 3.1 更新 `docs/workbench-navigation.md`
- [x] 3.2 更新 `docs/design.md` 和 `docs/p0.md`
- [x] 3.3 如新增产品/架构术语，更新 `CONTEXT.md`

## 4. Verification

- [x] 4.1 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
- [x] 4.2 Warden 审查确认没有引入真实 page stack 或行为扩张
