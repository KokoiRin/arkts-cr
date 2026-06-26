import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import handoff as handoff_module
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
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


class ProblemDiffViewCommandTests(unittest.TestCase):

    def test_browser_command_executor_views_selected_task_problem_diff(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0), FileChange("src/Two.ets", 1, 0)],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
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
            lines = [
                "File 2/2  src/Two.ets",
                "  @@ -1,2 +1,3 @@",
                "     1    1 | one",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(
                            parse_browser_command("view problem diff")
                        )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Opened problem diff src/Two.ets:2.", state.status_message)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
    def test_browser_command_executor_views_selected_task_output_problem_diff(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0), FileChange("src/Two.ets", 1, 0)],
                page=BrowserPage.TASK_OUTPUT,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
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
            lines = [
                "File 2/2  src/Two.ets",
                "  @@ -1,2 +1,3 @@",
                "     1    1 | one",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(
                            parse_browser_command("view problem diff")
                        )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 2)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
    def test_browser_command_executor_reports_problem_diff_without_changed_file(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Two.ets:2:1 error"],
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
                result = executor.execute(parse_browser_command("view problem diff"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.selected, 0)
        self.assertIn(
            "No diff for problem src/Two.ets:2 in current review scope.",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
