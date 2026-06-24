## 1. Task command model

- [x] 1.1 增加 task kind 和命令解析 helper
- [x] 1.2 为 `--test-cmd` / `CR_TEST_CMD` 与 `--lint-cmd` / `CR_LINT_CMD` 增加 CLI 配置
- [x] 1.3 保留 DouyinHarmony build 默认命令，不为 test/lint 猜测默认命令

## 2. Browser behavior

- [x] 2.1 支持 `test` / `tests` 启动后台 test 任务
- [x] 2.2 支持 `lint` 启动后台 lint 任务
- [x] 2.3 让面板标题、状态文案、停止文案和历史记录显示 task kind
- [x] 2.4 让 `stop` / `cancel` 操作当前任务
- [x] 2.5 让 `rerun` / `rebuild` 重跑最近任务 kind
- [x] 2.6 更新 command palette 和紧凑 help

## 3. Documentation

- [x] 3.1 更新 README 使用说明
- [x] 3.2 更新 `docs/design.md` 和 `docs/p0.md`

## 4. Verification

- [x] 4.1 增加任务命令解析、面板、history、rerun 和 browser loop 测试
- [x] 4.2 运行单元测试、编译检查、OpenSpec strict 校验和 diff 检查
