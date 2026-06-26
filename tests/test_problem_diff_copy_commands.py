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


class ProblemDiffCopyCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_selected_task_problem_diff(self):
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
                problem_scroll=1,
                selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error TS2: bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"files": [{"path": "src/Two.ets"}]},
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Two.ets\n\n```diff\n+two\n```",
                    ):
                        with patch(
                            "cr.ui.browser.file_actions.copy_text",
                            return_value=None,
                        ) as copy_text:
                            result = executor.execute(
                                parse_browser_command("copy problem diff")
                            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 1)
        self.assertEqual(state.problem_scroll, 1)
        self.assertEqual(state.selected, 0)
        copied = copy_text.call_args.args[0]
        self.assertIn("# File Diff: src/Two.ets", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(build_data.call_args.args[0][0].path, "src/Two.ets")
        self.assertIn("Copied problem diff src/Two.ets:2.", state.status_message)
    def test_browser_command_executor_copies_file_detail_current_row_problem_diff(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text(
                "one\ntwo\nthree\nfour\n",
                encoding="utf-8",
            )
            (source_dir / "Two.ets").write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0), FileChange("src/Two.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:4:1 error E1: bad one",
                        "src/Two.ets:2:1 error E2: bad two",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/2  src/One.ets",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.build_review_data",
                        return_value={"files": [{"path": "src/One.ets"}]},
                    ) as build_data:
                        with patch(
                            "cr.ui.browser.render_file_diff_snippet",
                            return_value="# File Diff: src/One.ets\n\n```diff\n+four\n```",
                        ):
                            with patch(
                                "cr.ui.browser.file_actions.copy_text",
                                return_value=None,
                            ) as copy_text:
                                result = executor.execute(
                                    parse_browser_command(
                                        "copy problem diff",
                                        raw_keys=True,
                                    )
                                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("# File Diff: src/One.ets", copied)
        self.assertNotIn("src/Two.ets", copied)
        self.assertEqual(build_data.call_args.args[0][0].path, "src/One.ets")
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.problem_selected, 1)
        self.assertIn("Copied problem diff src/One.ets:4.", state.status_message)
    def test_browser_command_executor_does_not_copy_file_detail_row_problem_diff_without_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text(
                "one\ntwo\nthree\nfour\n",
                encoding="utf-8",
            )
            (source_dir / "Two.ets").write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0), FileChange("src/Two.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Two.ets:2:1 error E2: bad two"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/2  src/One.ets",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser.build_review_data") as build_data:
                        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                            result = executor.execute(
                                parse_browser_command(
                                    "copy problem diff",
                                    raw_keys=True,
                                )
                            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        build_data.assert_not_called()
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn(
            "No current file problem diff to copy.",
            state.status_message,
        )
    def test_browser_command_executor_does_not_copy_problem_diff_without_changed_file(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("two\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Two.ets:2:1 error TS2: bad"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(
                        parse_browser_command("copy problem diff")
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn(
            "No diff for problem src/Two.ets:2 in current review scope.",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
