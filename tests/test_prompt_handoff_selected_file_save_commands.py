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


class PromptHandoffSelectedFileSaveCommandTests(unittest.TestCase):

    def test_browser_command_executor_saves_selected_file_prompt_explicit_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=False,
            )
            first_change = FileChange("src/First.ts", 2, 0)
            second_change = FileChange("src/Second.ts", 1, 1)
            state = BrowserState(
                [first_change, second_change],
                selected=1,
                page=BrowserPage.CHANGED_FILES,
                review_notes={
                    "src/First.ts": "not selected",
                    "src/Second.ts": "selected note",
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
                        "files": [{"path": "src/Second.ts"}],
                    },
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Second.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 3},
                        ):
                            with redirect_stdout(output):
                                result = executor.execute(
                                    parse_browser_command(
                                        "save prompt file tmp/second.md"
                                    )
                                )

            target = repo / "tmp" / "second.md"
            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "# Code Review Handoff\n\nsrc/Second.ts",
            )
            self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
            self.assertEqual(state.selected, 1)
            build_data.assert_called_once_with(
                [second_change],
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                include_hunks=True,
                other_changes={"staged": 0, "unstaged": 3},
                context=2,
                seen_paths=set(),
                review_notes={"src/Second.ts": "selected note"},
            )
            self.assertIn(
                "Saved prompt for 1 file to tmp/second.md",
                output.getvalue(),
            )
    def test_browser_command_executor_saves_selected_file_prompt_default_path(self):
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
            state = BrowserState(
                [FileChange("src/First.ts", 2, 0), FileChange("src/Second.ts", 1, 1)],
                selected=1,
                review_notes={"src/Second.ts": "selected note"},
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
                        "files": [{"path": "src/Second.ts"}],
                    },
                ):
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Second.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            with redirect_stdout(output):
                                result = executor.execute(
                                    parse_browser_command("save prompt file")
                                )

            target = repo / ".cr" / "handoff" / "review-prompt-file.md"
            self.assertTrue(result.handled)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "# Code Review Handoff\n\nsrc/Second.ts",
            )
            self.assertIn(
                "Saved prompt for 1 file to .cr/handoff/review-prompt-file.md",
                output.getvalue(),
            )

if __name__ == "__main__":
    unittest.main()
