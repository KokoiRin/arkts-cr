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


class TaskOutputEmptyStateTests(unittest.TestCase):

    def test_browser_command_executor_copy_task_reports_empty_state(self):
        # Behavior: 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task"))

        self.assertTrue(result.handled)
        copy.assert_not_called()
        self.assertIn("No task output to copy.", output.getvalue())
    def test_browser_command_executor_copy_task_tail_reports_empty_state(self):
        # Behavior: 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task tail"))

        self.assertTrue(result.handled)
        copy.assert_not_called()
        self.assertIn("No task output tail to copy.", output.getvalue())
    def test_browser_command_executor_copy_task_match_requires_find(self):
        # Behavior: 当用户在task output中复制空状态、任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["target failure"],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task match"))

        self.assertTrue(result.handled)
        copy.assert_not_called()
        self.assertIn("Run find TEXT first.", output.getvalue())
    def test_browser_command_executor_save_task_tail_reports_empty_state(self):
        # Behavior: 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("save task tail"))

            self.assertTrue(result.handled)
            self.assertFalse((repo / ".cr").exists())
            self.assertIn("No task output tail to save.", output.getvalue())
    def test_browser_command_executor_save_task_reports_empty_state(self):
        # Behavior: 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("save task"))

            self.assertTrue(result.handled)
            self.assertFalse((repo / ".cr").exists())
            self.assertIn("No task output to save.", output.getvalue())

if __name__ == "__main__":
    unittest.main()
