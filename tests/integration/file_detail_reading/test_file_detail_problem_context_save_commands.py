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


class FileDetailProblemContextSaveCommandTests(unittest.TestCase):

    def test_browser_command_executor_saves_file_detail_problem_context(self):
        # Behavior: 当用户在File Detail中保存「BrowserCommandExecutor 保存 File Detail Problem Context」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -2,2 +2,3 @@",
                "     2    2 | two",
                "          3 | +three",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.build_review_data",
                        return_value={"files": [{"path": "src/Sample.ts"}]},
                    ):
                        with patch(
                            "cr.ui.browser.render_file_diff_snippet",
                            return_value="# File Diff: src/Sample.ts",
                        ):
                            result = executor.execute(
                                parse_browser_command(
                                    "save problem context tmp/file-detail.md",
                                    raw_keys=True,
                                )
                            )

            saved = repo / "tmp" / "file-detail.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Problem Context: src/Sample.ts:3", text)
        self.assertIn("> 3  three", text)
        self.assertIn("# File Diff: src/Sample.ts", text)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("Saved problem context to tmp/file-detail.md.", state.status_message)
    def test_browser_command_executor_saves_file_detail_problem_context_with_current_problem(self):
        # Behavior: 当用户在File Detail中保存「BrowserCommandExecutor 保存 File Detail Problem Context with 当前问题」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "compile started",
                        "src/Sample.ts:4:1 warning W1: warn title",
                        "compile failed",
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
                "File 1/1  src/Sample.ts",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.build_review_data",
                        return_value={"files": [{"path": "src/Sample.ts"}]},
                    ):
                        with patch(
                            "cr.ui.browser.render_file_diff_snippet",
                            return_value="# File Diff: src/Sample.ts",
                        ):
                            result = executor.execute(
                                parse_browser_command(
                                    "save problem context tmp/file-detail-problem.md",
                                    raw_keys=True,
                                )
                            )

            saved = repo / "tmp" / "file-detail-problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("## Problem", text)
        self.assertIn("Severity: warning", text)
        self.assertIn("Code: W1", text)
        self.assertIn("warn title", text)
        self.assertIn("## Task Output", text)
        self.assertIn("> 2  src/Sample.ts:4:1 warning W1: warn title", text)
        self.assertIn("> 4  four", text)
        self.assertIn("# File Diff: src/Sample.ts", text)
        self.assertIn(
            "Saved problem context to tmp/file-detail-problem.md.",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
