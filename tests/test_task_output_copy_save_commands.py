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


class TaskOutputCopySaveCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_task_output(self):
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
    def test_browser_command_executor_copy_task_reports_empty_state(self):
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
    def test_browser_command_executor_copies_task_output_tail(self):
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
    def test_browser_command_executor_copy_task_tail_reports_empty_state(self):
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
    def test_browser_command_executor_copies_task_output_match(self):
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
    def test_browser_command_executor_copy_task_match_requires_find(self):
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
    def test_browser_command_executor_saves_task_output(self):
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
    def test_browser_command_executor_save_task_tail_reports_empty_state(self):
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
