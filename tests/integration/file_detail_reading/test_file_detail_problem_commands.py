import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cr.ui.browser as browser_module
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


class FileDetailProblemCommandTests(unittest.TestCase):
    def test_browser_command_executor_steps_file_detail_problem_to_visible_diff_line(self):
        # Behavior: 当用户在File Detail中执行操作「BrowserCommandExecutor steps File Detail 问题 to 可见 diff 行」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            (source_dir / "Other.ets").write_text("one\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/Other.ets:1:1 error",
                        "src/Foo.ets:2:1 error",
                        "src/Foo.ets:3:1 error",
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
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,3 +1,4 @@",
                "     1    1 | one",
                "          2 | +two",
                "     2    3 | three",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 1)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("已选择当前文件问题 1/2 src/Foo.ets:2。", state.status_message)
    def test_browser_command_executor_steps_file_detail_previous_problem(self):
        # Behavior: 当用户在File Detail中执行操作「BrowserCommandExecutor steps File Detail previous 问题」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/Foo.ets:2:1 error",
                        "src/Foo.ets:3:1 error",
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
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,3 +1,4 @@",
                "     1    1 | one",
                "          2 | +two",
                "     2    3 | three",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("已选择当前文件问题 1/2 src/Foo.ets:2。", state.status_message)
    def test_browser_command_executor_steps_file_detail_problem_without_visible_diff_line(self):
        # Behavior: 当用户在File Detail中执行操作「BrowserCommandExecutor steps File Detail 问题 不包含 可见 diff 行」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:3:1 error"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,1 +1,2 @@",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn(
            "已选择当前文件问题 1/1 src/Foo.ets:3，但当前 diff 不显示该行。",
            state.status_message,
        )
    def test_browser_command_executor_reports_file_detail_without_file_problems(self):
        # Behavior: 当用户在File Detail中处理异常「BrowserCommandExecutor 提示 File Detail 不包含 文件 问题」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Other.ets").write_text("one\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ets:1:1 error"],
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
                result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("当前文件没有任务问题。", state.status_message)

if __name__ == "__main__":
    unittest.main()
