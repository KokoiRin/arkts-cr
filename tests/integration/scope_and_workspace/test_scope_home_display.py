import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui import page_content
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


class ScopeHomeDisplayTests(unittest.TestCase):

    def test_browse_screen_scope_home_shows_review_scope_entries(self):
        # Behavior: 当用户在scope home中展示范围首页时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="scopes")
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: scope home", text)
        self.assertNotIn("Scope: scope home > Files", text)
        self.assertIn("Review scopes", text)
        self.assertIn("Worktree", text)
        self.assertIn("Staged", text)
        self.assertIn("All local changes", text)
        self.assertIn("Recent commits", text)
        self.assertIn("Base ref", text)
        self.assertIn(": base REF", text)
        self.assertIn("Explicit range", text)
        self.assertIn(": range OLD..NEW", text)
    def test_scope_home_screen_shows_live_scope_counts(self):
        # Behavior: 当用户在scope home中展示范围首页时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        state = BrowserState(
            [],
            page=BrowserPage.SCOPE_HOME,
            scope_counts={
                "worktree": 2,
                "staged": 1,
                "all": 3,
                "commits": 4,
            },
        )

        lines = page_content.browse_scope_home_screen_lines(
            state,
            TerminalStyle(),
            max_lines=20,
        )
        text = "\n".join(lines)

        self.assertIn("Worktree (2 files)", text)
        self.assertIn("Staged (1 file)", text)
        self.assertIn("All local changes (3 files)", text)
        self.assertIn("Recent commits (4 commits)", text)
        self.assertNotIn("Base ref (", text)
        self.assertNotIn("Explicit range (", text)

if __name__ == "__main__":
    unittest.main()
