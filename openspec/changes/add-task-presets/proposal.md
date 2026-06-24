## Why

`cr browse` 已支持 build / test / lint，但 test/lint 目前必须每次通过 CLI 参数或环境变量配置。要让它更像 IDE 的项目任务面板，需要仓库本地任务预设，让常用任务随项目一起定义，并保持当前命令优先级可解释。

## What Changes

- 增加项目本地 `.cr/tasks.json` 任务预设文件，支持 `build`、`test`、`lint` 三个字符串命令。
- 让 `cr.ui.tasks` 在解析任务命令时读取项目预设。
- 保持优先级：CLI 参数 > 环境变量 > 项目 preset > DouyinHarmony build 默认 > missing-command 提示。
- 对无效 JSON、非对象 JSON、非字符串命令值采取忽略策略，不阻断浏览器启动。
- 不新增 task kind，不实现多 profile，不新增 UI 编辑器，不改变已有命令和环境变量。

## Capabilities

### New Capabilities

- `browser-task-presets`: 定义浏览器 Task Runtime 如何发现和应用项目本地 build/test/lint 任务预设。

### Modified Capabilities

无。

## Impact

- 影响 `src/cr/ui/tasks.py` 的 task command resolution。
- 需要补充 task preset 单元测试和文档说明。
- 无新增运行时依赖，无 CLI 参数变化，无 workspace-state 格式变化。
