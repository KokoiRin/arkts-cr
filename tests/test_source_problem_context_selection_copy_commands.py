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


class SourceProblemContextSelectionCopyCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_selected_source_problem_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                source_selection_start=3,
                source_selection_end=6,
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
                    return_value={"files": [{"path": "src/Foo.ets"}]},
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
                    ):
                        with patch(
                            "cr.ui.browser.file_actions.copy_text",
                            return_value=None,
                        ) as copy_text:
                            result = executor.execute(
                                parse_browser_command("copy problem context")
                            )

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("# Problem Context: src/Foo.ets:5", copied)
        self.assertIn("src/Foo.ets:3-6", copied)
        self.assertIn("  3  line 3", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 2", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)
    def test_browser_command_executor_copies_selected_source_problem_context_with_current_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                source_selection_start=3,
                source_selection_end=6,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:5:1 warning W1: warn call"],
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
                    return_value={"files": [{"path": "src/Foo.ets"}]},
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
                    ):
                        with patch(
                            "cr.ui.browser.file_actions.copy_text",
                            return_value=None,
                        ) as copy_text:
                            result = executor.execute(
                                parse_browser_command("copy problem context")
                            )

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("## Problem", copied)
        self.assertIn("Severity: warning", copied)
        self.assertIn("Code: W1", copied)
        self.assertIn("warn call", copied)
        self.assertIn("## Task Output", copied)
        self.assertIn("> 1  src/Foo.ets:5:1 warning W1: warn call", copied)
        self.assertIn("src/Foo.ets:3-6", copied)
        self.assertIn("  3  line 3", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertNotIn("line 2", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)

if __name__ == "__main__":
    unittest.main()
