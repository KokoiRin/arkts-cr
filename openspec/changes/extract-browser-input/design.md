## Context

`browser.py` 现在还直接知道终端输入协议的细节：

- 如何判断 raw-key mode 是否可用。
- raw-key idle tick 用哪个 timeout。
- `input(prompt)` 遇到 EOF / KeyboardInterrupt 时返回什么 sentinel。
- ANSI escape sequence 如何映射到 `up` / `down` / `pageup` 等 browser command text。
- `/` 和 `:` 在 raw-key mode 中如何转换为 prompt command tokens。

These rules are stable enough to hide behind a deeper in-process module. There is no external adapter and no new dependency.

```text
Browser run loop -> Browser Input -> command/query/sentinel text
```

## Goals / Non-Goals

**Goals:**

- 新增 `cr.ui.input`，作为 browser terminal input protocol 的 implementation owner。
- 保留 `browser.py` 的 `_use_raw_keys`、`_read_browse_command`、`_read_filter_query`、`_read_command_query`、`_read_raw_key` wrappers，降低测试迁移成本。
- 把 sentinel 常量集中命名，减少 browser loop 对 magic strings 的直接知识。
- 保持 raw-key 读取不输出普通换行，保持 temporary line input 取消后完整 redraw 的现有行为。

**Non-Goals:**

- 不改变 `run_browser` 的 command handling、filter handling、workspace save-on-exit 或 frame dirty 语义。
- 不引入 curses、Rich、Textual、prompt_toolkit 或其他 TUI/input framework。
- 不改变 command names、key aliases、escape sequence mapping、prompt 文案或 line-mode compatibility。

## Module Interface

`cr.ui.input` should expose:

- `TICK`, `EOF_COMMAND`, `INTERRUPT`
- `FILTER_PROMPT_COMMAND`, `COMMAND_PROMPT_COMMAND`
- `use_raw_keys(stdin, stdout) -> bool`
- `read_browse_command(prompt, raw_keys, tick_when_idle, raw_key_reader=read_raw_key) -> str`
- `read_filter_query(prompt="filter> ") -> str`
- `read_command_query() -> str`
- `read_raw_key(stdin, timeout=None) -> str`

`browser.py` remains the owner of what those returned strings mean in product state. It may keep compatibility wrappers so existing tests can patch browser-level helper names.

## Behavior Preservation

This is an extraction, not a product change. It should preserve:

- non-TTY `input(prompt).strip()` behavior
- EOF returning `__eof__`
- KeyboardInterrupt returning `__interrupt__` and printing one newline
- idle timeout returning `__tick__`
- arrow/Home/End/PgUp/PgDn escape mapping
- raw `j/k/l/h/u/d/space//:/Ctrl-D` mapping
- raw-key normal reads not emitting a newline
- temporary command/filter prompt cancellation forcing a full browser redraw through existing run-loop logic

## Risks / Trade-offs

- **Risk:** compatibility wrappers leave two names for the same behavior.
  **Mitigation:** wrappers only delegate and exist for current tests/patches; implementation owner is `cr.ui.input`.

- **Risk:** `read_raw_key` depends on real TTY behavior and is hard to test end-to-end.
  **Mitigation:** keep the same implementation shape and test the injectable `read_browse_command` path plus existing browser raw-key tests.

- **Risk:** extracting only input still leaves `browser.py` large.
  **Mitigation:** this is a narrow seam with direct experience value; selected-file action extraction remains a later P0 candidate.
