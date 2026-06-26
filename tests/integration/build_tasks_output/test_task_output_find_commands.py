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


class TaskOutputFindCommandTests(unittest.TestCase):
    def test_browser_command_executor_finds_text_in_task_output(self):
        # Behavior: 当用户在task output中查找任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["compile ok", "\033[31mERROR target\033[0m", "done"],
                returncode=1,
            ),
            file_find_text="file-query",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._max_task_output_scroll", return_value=10):
            result = executor.execute(parse_browser_command("find target", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertEqual(state.task_scroll, 1)
        self.assertEqual(state.task_find_text, "target")
        self.assertEqual(state.file_find_text, "file-query")
        self.assertIn('Found "target" at line 2.', state.status_message)
    def test_browser_command_executor_repeats_task_output_find_matches(self):
        # Behavior: 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["target first", "context", "target second"],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._max_task_output_scroll", return_value=10):
            find = executor.execute(parse_browser_command("find target", raw_keys=True))
            next_match = executor.execute(
                parse_browser_command("next match", raw_keys=True)
            )
            scroll_after_next = state.task_scroll
            previous_match = executor.execute(
                parse_browser_command("prev match", raw_keys=True)
            )

        self.assertTrue(find.needs_redraw)
        self.assertTrue(next_match.needs_redraw)
        self.assertTrue(previous_match.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertEqual(scroll_after_next, 2)
        self.assertEqual(state.task_scroll, 0)
        self.assertEqual(state.task_find_text, "target")
        self.assertIn('Found "target" at line 1.', state.status_message)
    def test_browser_command_executor_reports_task_output_find_empty_states(self):
        # Behavior: 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_OUTPUT)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        no_task = executor.execute(parse_browser_command("find target", raw_keys=True))

        self.assertTrue(no_task.handled)
        self.assertTrue(no_task.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertIn("No task output to find.", state.status_message)

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state.task = TaskState(["./build.sh"], process, lines=["compile ok"])
        empty = executor.execute(parse_browser_command("find", raw_keys=True))
        missing = executor.execute(parse_browser_command("find owner", raw_keys=True))
        repeat = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(empty.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertTrue(repeat.needs_redraw)
        self.assertEqual(state.task_find_text, "owner")
        self.assertIn('No matches for "owner".', state.status_message)

if __name__ == "__main__":
    unittest.main()
