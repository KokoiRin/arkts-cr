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


class ScopeHomeSelectionTests(unittest.TestCase):

    def test_scope_home_enter_switches_to_staged_scope(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        frames: list[tuple[str, bool, bool]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, args.staged, args.all_changes))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["scopes", "down", "enter", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("list", True, False), frames)
    def test_scope_home_enter_opens_recent_commits(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.mode)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch(
                                "cr.ui.browser._load_recent_commits",
                                return_value=[
                                    CommitSummary(
                                        commit="abcdef1234567890",
                                        parent="1234567890abcdef",
                                        authored_at="2026-06-24",
                                        subject="Example change",
                                    )
                                ],
                            ):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=[
                                            "scopes",
                                            "down",
                                            "down",
                                            "down",
                                            "enter",
                                            "q",
                                        ],
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen",
                                            side_effect=capture_draw,
                                        ):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn("commits", frames)
    def test_home_key_still_jumps_to_first_file_instead_of_opening_scope_home(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        frames: list[tuple[str, int]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, state.selected))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[
                            FileChange("src/First.ts", 1, 0),
                            FileChange("src/Second.ts", 1, 0),
                        ],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["down", "home", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("list", 1), frames)
        self.assertEqual(frames[-1], ("list", 0))

if __name__ == "__main__":
    unittest.main()
