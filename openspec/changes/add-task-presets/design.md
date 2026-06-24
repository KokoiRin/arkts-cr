## Context

Task Runtime 已经集中在 `cr.ui.tasks`，这是引入项目本地任务预设的合适位置。当前 build/test/lint 的命令来源分散在 CLI 参数、环境变量和 DouyinHarmony 默认 build 规则里；缺少仓库自带配置，导致日常项目任务无法像 IDE 一样随项目打开即用。

## Goals / Non-Goals

**Goals:**

- 支持仓库根目录 `.cr/tasks.json`。
- 支持三个 key：`build`、`test`、`lint`，每个值是 shell-like command string。
- 在 `task_command()` 中统一应用预设。
- 保持优先级：CLI 参数 > 环境变量 > 项目 preset > DouyinHarmony build 默认 > missing。
- 无效 preset 文件不阻断浏览器启动。

**Non-Goals:**

- 不支持 profiles、variants、参数化 task、依赖 task、并发 task。
- 不新增 UI 编辑配置。
- 不改变命令 prompt、command palette 文案或 task panel 渲染。
- 不引入 TOML/YAML 第三方依赖。

## Decisions

### 1. 使用 `.cr/tasks.json`

选择：在 repo root 下读取 `.cr/tasks.json`，格式为：

```json
{
  "build": "./remote buildEntry --app douyin",
  "test": "npm test",
  "lint": "npm run lint"
}
```

原因：JSON 是 Python 标准库能力；当前只需要三条字符串命令，JSON 足够表达，迁移到其他语言也容易。

替代方案：`.cr/tasks.toml` 或 YAML。暂不采用，因为会引入依赖或解析差异，当前收益不足。

### 2. 预设只影响缺省命令来源

选择：`task_command(repo, args, kind)` 的优先级为 CLI 参数、环境变量、项目 preset、DouyinHarmony build 默认、missing。

原因：CLI 参数和环境变量适合临时覆盖；项目 preset 是日常默认；DouyinHarmony 默认是历史兼容兜底。

替代方案：项目 preset 覆盖环境变量。暂不采用，因为这会让 CI 或个人 shell override 变难解释。

### 3. 无效 preset 静默忽略

选择：缺失文件、无效 JSON、非对象 JSON、非字符串值都忽略。

原因：task preset 是体验增强，不能让 review/browser 因一个坏配置无法启动。具体错误 UI 可以以后做配置诊断页。

替代方案：在 Task Panel 显示配置错误。暂不采用，因为本 P0 不做配置 UI，且会影响现有 task command 缺省提示。

## Risks / Trade-offs

- [Risk] 静默忽略可能让用户不知道配置写错。→ Mitigation：本轮文档明确格式；后续可加 `tasks` 配置诊断命令。
- [Risk] JSON 不能写注释。→ Mitigation：当前配置足够小；如果真实项目需要注释/复杂结构，再迁移 schema。
- [Risk] shell-like string 在不同平台有差异。→ Mitigation：沿用现有 `shlex.split` 语义，保持与 CLI/env 配置一致。
