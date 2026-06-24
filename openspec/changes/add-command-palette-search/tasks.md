## 1. Palette Filter State

- [x] 1.1 给 `BrowserState` 增加 `command_filter_text`
- [x] 1.2 增加 `_filtered_command_palette_entries(state)`，按 group/label/command/description 过滤
- [x] 1.3 让 commands mode 的 selection/clamp/scroll 基于过滤后的 entries

## 2. Input And Rendering

- [x] 2.1 raw-key commands mode 下 `/` 写入 command filter，而不是文件 filter
- [x] 2.2 raw-key commands mode 下 `c` / `clear` 清 command filter，而不是文件 filter
- [x] 2.3 command palette 渲染 filter 状态和空结果
- [x] 2.4 过滤后 Enter 执行当前过滤结果中的命令

## 3. Documentation

- [x] 3.1 更新 README，说明 command palette 内 `/` 搜索和 `c` 清除
- [x] 3.2 更新 `docs/design.md` 和 `docs/p0.md`，记录本轮 P0

## 4. Verification

- [x] 4.1 增加 filter helper、渲染、输入隔离、清除和执行测试
- [x] 4.2 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
