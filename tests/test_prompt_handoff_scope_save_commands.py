import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.review.prompt import render_prompt_handoff
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
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


class PromptHandoffScopeSaveCommandTests(unittest.TestCase):

    def test_browser_command_executor_saves_visible_scope_prompt_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=3,
                paths=[],
                code=False,
                untracked=True,
            )
            src_change = FileChange("src/Sample.ts", 2, 1)
            docs_change = FileChange("docs/Guide.md", 1, 0)
            state = BrowserState(
                [src_change, docs_change],
                selected=0,
                page=BrowserPage.FILE_DETAIL,
                filter_text="src",
                seen_paths={"src/Sample.ts"},
                review_notes={
                    "src/Sample.ts": "check lifecycle",
                    "docs/Guide.md": "outside filtered handoff",
                },
            )
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={
                        "summary": {"files": 1},
                        "files": [{"path": "src/Sample.ts"}],
                    },
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Sample.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                                with redirect_stdout(output):
                                    result = executor.execute(
                                        parse_browser_command("save prompt")
                                    )

            target = repo / ".cr" / "handoff" / "review-prompt.md"
            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertEqual(target.read_text(encoding="utf-8"), "# Code Review Handoff\n\nsrc/Sample.ts")
            self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
            self.assertEqual(state.selected, 0)
            self.assertEqual(state.filter_text, "src")
            self.assertIsNone(state.task)
            build_data.assert_called_once_with(
                [src_change],
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                include_hunks=True,
                other_changes={"staged": 0, "unstaged": 0},
                context=3,
                seen_paths={"src/Sample.ts"},
                review_notes={"src/Sample.ts": "check lifecycle"},
            )
            copy.assert_not_called()
            self.assertIn(
                "Saved prompt for 1 file to .cr/handoff/review-prompt.md",
                output.getvalue(),
            )
    def test_browser_command_executor_does_not_save_empty_scope_prompt(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState([])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.build_review_data") as build_data:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("save prompt"))

            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            build_data.assert_not_called()
            self.assertFalse((repo / ".cr" / "handoff" / "review-prompt.md").exists())
            self.assertIn("No changed files to save prompt.", output.getvalue())

if __name__ == "__main__":
    unittest.main()
