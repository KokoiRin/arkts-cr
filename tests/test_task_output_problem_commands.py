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


class TaskOutputProblemCommandTests(unittest.TestCase):
    def test_browser_command_executor_opens_task_output_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=12,
            task_scroll=9,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("task output"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertEqual(state.task_scroll, 0)

        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 12)
    def test_browser_command_executor_moves_task_output_problem_selection(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (source_dir / name).write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_OUTPUT,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "plain line",
                        "src/Two.ets:2:1 error",
                        "plain line",
                        "src/Three.ets:3:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(False),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                next_result = executor.execute(parse_browser_command("next problem"))
                selected_after_next = state.problem_selected
                scroll_after_next = state.task_scroll
                prev_result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(next_result.handled)
        self.assertTrue(next_result.needs_redraw)
        self.assertEqual(selected_after_next, 1)
        self.assertGreaterEqual(scroll_after_next, 1)
        self.assertTrue(prev_result.handled)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
    def test_browser_command_executor_views_selected_task_output_problem_source(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("one\ntwo\nthree\n", encoding="utf-8")
            second.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_OUTPUT,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:2:1 error",
                        "src/Two.ets:2:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.problem_selected, 1)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
    def test_browser_command_executor_reports_task_output_view_without_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(["./build.sh"], process, lines=["plain failure"]),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertIn("No task problem to view.", state.status_message)
    def test_browser_command_executor_scrolls_task_output_page(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                lines=[f"line {index}" for index in range(30)],
                returncode=0,
            ),
            page=BrowserPage.TASK_OUTPUT,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(False),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            page_down = executor.execute(parse_browser_command("pagedown"))
            self.assertTrue(page_down.needs_redraw)
            self.assertGreater(state.task_scroll, 0)

            executor.execute(parse_browser_command("home"))
            self.assertEqual(state.task_scroll, 0)

            executor.execute(parse_browser_command("end"))
            self.assertGreater(state.task_scroll, 0)

if __name__ == "__main__":
    unittest.main()
