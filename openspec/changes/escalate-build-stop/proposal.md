## Why

`cr browse` 现在会把后台 build 放进独立进程组，并在 `stop` / `cancel` 时发送温和终止信号。但真实构建工具可能忽略或延迟处理 `SIGTERM`。如果进程组一直不退出，底部 build 面板会长期停留在 stopping，构建日志也可能继续干扰用户浏览代码。

为了让 `cr` 更像 IDE 中可控的任务面板，停止动作需要有明确的最终态：先温和终止，过了短宽限期仍未退出时升级为强制终止。

## What Changes

- `stop` / `cancel` 记录停止请求时间。
- `_poll_build` 在 build 处于 stopping 且超过宽限期时，对 build 进程组发送 `SIGKILL`。
- 强杀只执行一次，避免每轮刷新重复发信号或重复刷日志。
- build 面板显示可读的 escalation 文案。
- 保留现有 stopped / succeeded / failed 状态语义。

## Capabilities

### New Capabilities
- `build-stop-escalation`: 后台 build 停止后的宽限期和强制终止行为。

### Modified Capabilities
- `build-process-group-lifecycle`: 停止进程组后如果仍在运行，会升级到强杀。

## Impact

- 主要影响 `src/cr/ui/browser.py` 的 `BuildState`、`_stop_build` 和 `_poll_build`。
- 测试需要覆盖停止时间记录、超时后 `SIGKILL`、只升级一次、无进程组时不崩溃。
- 文档需要说明 `stop` 会先温和停止，必要时升级强杀。
