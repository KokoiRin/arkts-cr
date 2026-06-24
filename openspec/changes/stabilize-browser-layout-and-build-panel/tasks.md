## 1. Layout Contract

- [x] 1.1 增加 screen layout helper，统一计算主内容区、build 面板区和输入提示行
- [x] 1.2 让整屏重画和 build 局部刷新使用同一个 layout helper

## 2. Raw-Key Stability

- [x] 2.1 修正 raw-key 命令读取，普通按键不再输出额外换行
- [x] 2.2 保留 filter/command 显式行输入，并确保下一帧恢复固定区域渲染

## 3. Verification And Documentation

- [x] 3.1 增加布局、build 局部刷新和 raw-key 不滚屏测试
- [x] 3.2 更新 README、`docs/design.md` 和 `docs/p0.md`，记录产品定位、页面层级和本轮 P0
- [x] 3.3 运行单元测试、编译检查和 OpenSpec 校验
