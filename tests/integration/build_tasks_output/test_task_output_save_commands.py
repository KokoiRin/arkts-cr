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


class TaskOutputSaveCommandTests(unittest.TestCase):

    def test_browser_command_executor_saves_task_output(self):
        # Behavior: 当用户在task output中保存任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=["compile line"],
                returncode=0,
            ),
        )
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
                    result = executor.execute(parse_browser_command("save task tmp/task.md"))

            target = repo / "tmp" / "task.md"
            self.assertTrue(result.handled)
            self.assertIn("# Build output", target.read_text(encoding="utf-8"))
            self.assertIn("Saved task output to tmp/task.md", output.getvalue())
    def test_browser_command_executor_saves_task_output_tail(self):
        # Behavior: 当用户在task output中保存任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=[f"line {index}" for index in range(1, 45)],
                returncode=1,
            ),
        )
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

            target = repo / ".cr" / "handoff" / "task-output-tail.md"
            saved_text = target.read_text(encoding="utf-8")
            self.assertTrue(result.handled)
            self.assertIn("# Build output tail", saved_text)
            self.assertNotIn("\nline 4\n", saved_text)
            self.assertIn("line 44", saved_text)
            self.assertIn(
                "Saved task output tail to .cr/handoff/task-output-tail.md",
                output.getvalue(),
            )
    def test_browser_command_executor_saves_task_output_match_default_path(self):
        # Behavior: 当用户在task output中保存任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task_scroll=1,
            task_find_text="target",
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=["compile started", "target failure", "compile stopped"],
                returncode=1,
            ),
        )
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
                    result = executor.execute(parse_browser_command("save task match"))

            target = repo / ".cr" / "handoff" / "task-output-match.md"
            saved_text = target.read_text(encoding="utf-8")
            self.assertTrue(result.handled)
            self.assertIn("# Build output match", saved_text)
            self.assertIn("> 2  target failure", saved_text)
            self.assertIn(
                "Saved task output match to .cr/handoff/task-output-match.md",
                output.getvalue(),
            )

if __name__ == "__main__":
    unittest.main()
