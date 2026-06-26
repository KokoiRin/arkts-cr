import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
    _draw_browse_screen,
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


class FileDetailRefreshRenderingTests(unittest.TestCase):
    def test_refresh_preserves_file_detail_when_selected_file_survives(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 1),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
            page=BrowserPage.FILE_DETAIL,
            file_scroll=20,
        )
        state.file_line_cache["stale"] = ["old"]
        state.page_back_stack.append(
            browser_module.BrowserPageSnapshot(
                BrowserPage.CHANGED_FILES,
                0,
                0,
                0,
                0,
                0,
                0,
                "",
                None,
                0,
            )
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[
                FileChange("src/Second.ts", 3, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
        ):
            with patch("cr.ui.browser._show_commits_when_empty"):
                with patch("cr.ui.browser._max_file_scroll", return_value=8):
                    result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.changes[0].path, "src/Second.ts")
        self.assertEqual(state.file_scroll, 8)
        self.assertEqual(state.file_line_cache, {})
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])
    def test_refresh_returns_to_changed_files_when_file_detail_disappears(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        state = BrowserState(
            [FileChange("src/Old.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=12,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[FileChange("src/New.ts", 1, 0)],
        ):
            with patch("cr.ui.browser._show_commits_when_empty"):
                result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])
        self.assertIn("Current file no longer visible after refresh.", state.status_message)
    def test_browse_screen_file_detail_shows_product_breadcrumb(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
            context=2,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="file")
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with patch(
                    "cr.ui.browser.change_hunk_lines",
                    return_value=["changes:", "  3 + added"],
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Files > src/Sample.ts", text)
        self.assertIn("操作：]/[ 跳转 hunk", text)

if __name__ == "__main__":
    unittest.main()
