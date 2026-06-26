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


class FileDetailProblemContextCopyCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_file_detail_problem_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
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
                            with patch(
                                "cr.ui.browser.file_actions.copy_text",
                                return_value=None,
                            ) as copy_text:
                                result = executor.execute(
                                    parse_browser_command(
                                        "copy problem context",
                                        raw_keys=True,
                                    )
                                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("# Problem Context: src/Sample.ts:4", copied)
        self.assertNotIn("## Problem", copied)
        self.assertNotIn("## Task Output", copied)
        self.assertIn("Symbol: class Sample > method render", copied)
        self.assertIn("> 4      const title = 'new'", copied)
        self.assertIn("## Diff", copied)
        self.assertIn("# File Diff: src/Sample.ts", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Copied problem context src/Sample.ts:4.", state.status_message)
    def test_browser_command_executor_copies_file_detail_problem_context_with_current_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0), FileChange("src/Other.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "compile started",
                        "src/Sample.ts:4:1 error TS2322: bad title",
                        "compile continued",
                        "src/Other.ts:2:1 error TS9: other bad",
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
                "File 1/2  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
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
                            with patch(
                                "cr.ui.browser.file_actions.copy_text",
                                return_value=None,
                            ) as copy_text:
                                result = executor.execute(
                                    parse_browser_command(
                                        "copy problem context",
                                        raw_keys=True,
                                    )
                                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("# Problem Context: src/Sample.ts:4", copied)
        self.assertIn("## Problem", copied)
        self.assertIn("Severity: error", copied)
        self.assertIn("Code: TS2322", copied)
        self.assertIn("bad title", copied)
        self.assertIn("## Source", copied)
        self.assertIn("> 4      const title = 'new'", copied)
        self.assertIn("## Task Output", copied)
        self.assertIn("  1  compile started", copied)
        self.assertIn("> 2  src/Sample.ts:4:1 error TS2322: bad title", copied)
        self.assertIn("  3  compile continued", copied)
        self.assertIn("## Diff", copied)
        self.assertIn("# File Diff: src/Sample.ts", copied)
        self.assertNotIn("src/Other.ts", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 1)
        self.assertIn("Copied problem context src/Sample.ts:4.", state.status_message)

if __name__ == "__main__":
    unittest.main()
