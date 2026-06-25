## 为什么

Task Problems 已经能按文件分组，也能复制当前文件的问题，但在大型构建输出里，用户仍然需要一条快速路径在文件组之间跳转。现在只能逐条问题移动，文件多、每个文件问题多时扫描成本偏高。

## 变更内容

- 新增 `next problem file`，从当前选中问题跳到下一个不同文件的第一条可见问题。
- 新增 `prev problem file`，从当前选中问题跳到上一个不同文件的第一条可见问题。
- 两个命令都基于当前可见 Problems 列表工作，遵守 severity/text filter、sort、group。
- 在中文 help、action bar、command catalog、README 和 P0 文档中暴露。

## 影响

- 只影响 Task Problems 的选择移动。
- 不新增折叠状态、组级选择模型、quick-fix 执行、诊断持久化或工具专用 parser。
