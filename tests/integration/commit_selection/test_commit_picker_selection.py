import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import commit_picker, page_content
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
    _draw_browse_screen,
)
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import CommitSummary, FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class CommitPickerSelectionTests(unittest.TestCase):

    def test_commit_picker_opens_the_selected_filtered_commit(self):
        # Behavior: 当用户在Commit Picker中打开或定位「Commit Picker 打开 the 选中 filtered commit」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        commits = [
            CommitSummary(
                commit="1111111111111111",
                parent="0000000000000000",
                authored_at="2026-06-24",
                subject="Docs only",
            ),
            CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-25",
                subject="Feature login",
            ),
        ]

        self.assertIs(
            commit_picker.selected_commit(commits, selected=0, query="login"),
            commits[1],
        )
        self.assertIsNone(
            commit_picker.selected_commit(commits, selected=0, query="missing")
        )
        self.assertIsNone(commit_picker.selected_commit(commits, selected=9))
    def test_commit_picker_number_selects_filtered_commit(self):
        # Behavior: 当用户在Commit Picker中过滤「Commit Picker number 选择 filtered commit」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="1111111111111111",
                    parent="0000000000000000",
                    authored_at="2026-06-24",
                    subject="Docs only",
                ),
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-25",
                    subject="Feature login",
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="login",
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[FileChange("src/Login.ts", 1, 0)],
        ):
            result = executor.execute(parse_browser_command("1"))

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected_commit.subject, "Feature login")
        self.assertEqual(args.ref_range, "1234567890abcdef..abcdef1234567890")

if __name__ == "__main__":
    unittest.main()
