import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import input as browser_input
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
    _draw_browse_screen,
)
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class TaskOutputCopyCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_task_output(self):
        # Behavior: 当用户在task output中复制任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [],
            task=TaskState(
                ["npm", "test"],
                process,
                kind="test",
                lines=["failed test"],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copied_text = copy.call_args.args[0]
        self.assertIn("# Test output", copied_text)
        self.assertIn("failed test", copied_text)
        self.assertEqual(copy.call_args.args[1], "copy-tool")
        self.assertIn("Copied task output.", output.getvalue())
    def test_browser_command_executor_copies_task_output_tail(self):
        # Behavior: 当用户在task output中复制任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=[f"line {index}" for index in range(1, 7)],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task tail 2"))

        self.assertTrue(result.handled)
        copied_text = copy.call_args.args[0]
        self.assertIn("# Build output tail", copied_text)
        self.assertNotIn("line 4", copied_text)
        self.assertIn("line 5", copied_text)
        self.assertIn("line 6", copied_text)
        self.assertEqual(copy.call_args.args[1], "copy-tool")
        self.assertIn("Copied task output tail.", output.getvalue())
    def test_browser_command_executor_copies_task_output_match(self):
        # Behavior: 当用户在task output中复制任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task_scroll=4,
            task_find_text="target",
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=[f"line {index}" for index in range(1, 4)]
                + ["before target", "target failure", "after target"]
                + [f"line {index}" for index in range(7, 10)],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task match"))

        self.assertTrue(result.handled)
        copied_text = copy.call_args.args[0]
        self.assertIn("# Build output match", copied_text)
        self.assertIn("Query: target", copied_text)
        self.assertIn("  4  before target", copied_text)
        self.assertIn("> 5  target failure", copied_text)
        self.assertIn("  6  after target", copied_text)
        self.assertNotIn("line 9", copied_text)
        self.assertEqual(copy.call_args.args[1], "copy-tool")
        self.assertIn("Copied task output match.", output.getvalue())

if __name__ == "__main__":
    unittest.main()
