## 1. Frame State

- [x] 1.1 增加 `BrowserFrame`，记录上一次 raw-key layout、是否已有完整 frame、build 面板快照和 dirty 状态
- [x] 1.2 让完整 browser redraw 更新 frame 状态，并同步 build panel 快照
- [x] 1.3 让临时 command/filter line input 返回后强制下一帧 full redraw

## 2. Safe Partial Refresh

- [x] 2.1 让 build panel 局部刷新接收 frame 状态
- [x] 2.2 当 frame 不存在或 layout 已变化时，局部刷新不写终端，并要求 full redraw
- [x] 2.3 保持 build panel 内容未变化时不重复输出

## 3. Product Layering

- [x] 3.1 更新 README 的页面层级描述：一个 browser frame，四个固定区域，一个后台任务面板
- [x] 3.2 更新 `docs/design.md` 和 `docs/p0.md`，记录本轮 P0 和后续功能落层原则

## 4. Verification

- [x] 4.1 增加 frame redraw、过期 layout、line input 恢复、build tick 后导航的测试
- [x] 4.2 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
