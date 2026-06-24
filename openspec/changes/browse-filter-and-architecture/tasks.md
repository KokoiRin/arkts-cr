## 1. Browse Module

- [x] 1.1 新增 `src/cr/ui/browser.py`，承接 `cr browse` 的状态机、屏幕渲染、输入读取和打开编辑器逻辑
- [x] 1.2 将 `src/cr/cli.py` 的 `cmd_browse` 收敛为调用 browser module，并移除不再属于 CLI 入口的 imports/helpers

## 2. Filtering Behavior

- [x] 2.1 实现大小写不敏感的路径过滤，并让 selected index 始终 clamp 到 filtered view
- [x] 2.2 支持 raw-key TTY 中按 `/` 输入过滤条件，以及 `c` / `clear` 清除过滤
- [x] 2.3 支持非 TTY 行模式中的 `/query`、`filter query` 和清除过滤命令
- [x] 2.4 在列表界面展示 active filter、匹配数量和清除提示

## 3. Verification And Documentation

- [x] 3.1 增加过滤、刷新、非 TTY 兼容和 browser module 渲染测试
- [x] 3.2 更新 README、`docs/design.md` 和 `docs/p0.md`，记录新的 browse 过滤能力和 module 设计
- [x] 3.3 运行单元测试、编译检查和一次手动 smoke check
