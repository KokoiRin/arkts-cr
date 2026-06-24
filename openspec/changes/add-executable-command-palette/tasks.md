## 1. Palette State And Catalog

- [x] 1.1 增加 command palette entry 模型，派生可执行命令列表
- [x] 1.2 给 `BrowserState` 增加 commands mode selection/scroll，并让 clamp 支持 commands mode
- [x] 1.3 保持只读 command list 的非 TTY 输出兼容

## 2. Palette Rendering And Execution

- [x] 2.1 commands screen 渲染选中 marker、group、command 和 description
- [x] 2.2 raw-key commands mode 支持 ↑/↓ / j/k 移动
- [x] 2.3 raw-key commands mode Enter 执行选中命令，并避免误打开文件
- [x] 2.4 b/left 从 commands mode 返回 list，保留文件 selection

## 3. Documentation

- [x] 3.1 更新 README，说明 `: commands` 是可执行 command palette
- [x] 3.2 更新 `docs/design.md` 和 `docs/p0.md`，记录本轮 P0 和命令入口层级

## 4. Verification

- [x] 4.1 增加 palette entries、渲染、移动、执行和返回测试
- [x] 4.2 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
