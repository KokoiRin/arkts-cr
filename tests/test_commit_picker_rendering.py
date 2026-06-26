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


class CommitPickerRenderingTests(unittest.TestCase):

    def test_browse_screen_recent_commits_stays_scope_picker(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Example change",
                )
            ],
            page="commits",
        )
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: recent commits", text)
        self.assertNotIn("Scope: recent commits > Files", text)
    def test_commit_picker_rows_show_change_summary(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Example change",
                    files=2,
                    added=10,
                    deleted=3,
                )
            ],
            page=BrowserPage.COMMIT_PICKER,
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )

        self.assertIn("2 files, +10 -3", "\n".join(lines))
        self.assertIn("Example change", "\n".join(lines))
    def test_commit_picker_filter_shows_matches_and_count(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                    files=2,
                    added=10,
                    deleted=3,
                ),
                CommitSummary(
                    commit="1111111122222222",
                    parent="abcdef1234567890",
                    authored_at="2026-06-25",
                    subject="Docs only",
                    files=1,
                    added=1,
                    deleted=0,
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="login",
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn('Filter: login (1/2 matches, c to clear)', text)
        self.assertIn("Feature login", text)
        self.assertNotIn("Docs only", text)
    def test_commit_picker_filter_empty_state(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="missing",
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn("No recent commits match filter: missing (1 total).", text)
        self.assertIn("Press c to clear the filter.", text)
    def test_browse_screen_selected_commit_files_show_product_breadcrumb(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range="abcdef1^..abcdef1",
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            selected_commit=CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-24",
                subject="Example change",
            ),
        )
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        self.assertIn("Scope: commit abcdef12 > Files", output.getvalue())

if __name__ == "__main__":
    unittest.main()
