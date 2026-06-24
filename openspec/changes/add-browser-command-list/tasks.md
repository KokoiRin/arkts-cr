## 1. Command Catalog

- [x] 1.1 增加 browser command catalog helper，按用途返回命令分组
- [x] 1.2 增加 command list 渲染 helper，并适配小终端分页/截断

## 2. Command List View

- [x] 2.1 增加 `commands` mode，并让 `commands` / `cmds` / `help commands` 打开命令列表
- [x] 2.2 raw-key `:` 输入空值或 `?` 时打开命令列表
- [x] 2.3 从命令列表按 `b` / `back` 回到文件列表，并保留 build 面板

## 3. Verification And Documentation

- [x] 3.1 增加命令列表显示、入口别名、raw prompt 行为和返回行为测试
- [x] 3.2 更新 README、`docs/design.md` 和 `docs/p0.md`，记录 command list 能力
- [x] 3.3 运行单元测试、编译检查、OpenSpec 校验和 diff check
