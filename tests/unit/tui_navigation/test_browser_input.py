import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from cr.ui import input as browser_input
from cr.ui.browser import _read_browse_command


class BrowserInputTests(unittest.TestCase):
    def test_raw_key_command_read_does_not_print_newline(self):
        # Behavior: 当用户在产品行为中不执行input、raw、key、read时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        output = StringIO()

        with patch("cr.ui.browser._read_raw_key", return_value="down"):
            with redirect_stdout(output):
                command = _read_browse_command("cr:list> ", raw_keys=True)

        self.assertEqual(command, "down")
        self.assertEqual(output.getvalue(), "")

    def test_browser_input_raw_key_reader_does_not_print_newline(self):
        # Behavior: 当用户在产品行为中不执行input、input、raw、key时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在产品行为中验证input、input、line、mode时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在产品行为中验证input、input、idle、tick时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
