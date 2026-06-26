import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from cr.ui import input as browser_input
from cr.ui.browser import _read_browse_command


class BrowserInputTests(unittest.TestCase):
    def test_raw_key_command_read_does_not_print_newline(self):
        # Behavior: 当用户在TUI 导航中执行操作「raw-key 输入 命令 读取 不会 print newline」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        output = StringIO()

        with patch("cr.ui.browser._read_raw_key", return_value="down"):
            with redirect_stdout(output):
                command = _read_browse_command("cr:list> ", raw_keys=True)

        self.assertEqual(command, "down")
        self.assertEqual(output.getvalue(), "")

    def test_browser_input_raw_key_reader_does_not_print_newline(self):
        # Behavior: 当用户在TUI 导航中执行操作「browser 输入 raw-key 输入 读取器 不会 print newline」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        output = StringIO()

        with redirect_stdout(output):
            command = browser_input.read_browse_command(
                "cr:list> ",
                raw_keys=True,
                raw_key_reader=lambda timeout=None: "down",
            )

        self.assertEqual(command, "down")
        self.assertEqual(output.getvalue(), "")

    def test_browser_input_line_mode_returns_eof_and_interrupt_sentinels(self):
        # Behavior: 当用户在TUI 导航中执行操作「browser 输入 line-mode 返回 eof and interrupt sentinels」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        eof_output = StringIO()
        interrupt_output = StringIO()

        with patch("builtins.input", side_effect=EOFError):
            with redirect_stdout(eof_output):
                eof_command = browser_input.read_browse_command("cr:list> ", raw_keys=False)
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with redirect_stdout(interrupt_output):
                interrupt_command = browser_input.read_browse_command(
                    "cr:list> ",
                    raw_keys=False,
                )

        self.assertEqual(eof_command, browser_input.EOF_COMMAND)
        self.assertEqual(interrupt_command, browser_input.INTERRUPT)
        self.assertEqual(eof_output.getvalue(), "\n")
        self.assertEqual(interrupt_output.getvalue(), "\n")

    def test_browser_input_idle_tick_uses_raw_idle_timeout(self):
        # Behavior: 当用户在TUI 导航中执行操作「browser 输入 idle tick 使用 raw idle timeout」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        seen_timeouts = []

        command = browser_input.read_browse_command(
            "cr:list> ",
            raw_keys=True,
            tick_when_idle=True,
            raw_key_reader=lambda timeout=None: seen_timeouts.append(timeout)
            or browser_input.TICK,
        )

        self.assertEqual(command, browser_input.TICK)
        self.assertEqual(seen_timeouts, [browser_input.RAW_IDLE_TIMEOUT_SECONDS])
