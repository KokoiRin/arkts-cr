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


class ScopeHomeTests(unittest.TestCase):
    def test_browse_screen_scope_home_shows_review_scope_entries(self):
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

    def test_scope_home_command_opens_scope_home(self):
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
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["scopes", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn("scopes", frames)

    def test_scope_home_command_loads_scope_counts(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_scope_home_counts",
            return_value={"worktree": 2, "staged": 1, "all": 3, "commits": 4},
        ) as load_counts:
            result = executor.execute(parse_browser_command("scopes", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)
        self.assertEqual(state.scope_counts["worktree"], 2)
        load_counts.assert_called_once_with(args)

    def test_scope_home_refresh_reloads_scope_counts(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.SCOPE_HOME,
            scope_counts={"worktree": 1},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_scope_home_counts",
            return_value={"worktree": 4},
        ) as load_counts:
            result = executor.execute(parse_browser_command("r", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)
        self.assertEqual(state.scope_counts["worktree"], 4)
        load_counts.assert_called_once_with(args)

    def test_scope_home_count_loader_counts_review_scope_candidates(self):
        args = argparse_namespace(paths=["src"], code=True, untracked=True)

        def changed_files(paths, staged=False, all_changes=False, include_untracked=False):
            self.assertEqual(paths, ["src"])
            if staged:
                self.assertFalse(include_untracked)
                return [FileChange("src/Staged.ts", 1, 0)]
            if all_changes:
                self.assertTrue(include_untracked)
                return [
                    FileChange("src/Staged.ts", 1, 0),
                    FileChange("src/Unstaged.ts", 1, 0),
                    FileChange("README.md", 1, 0),
                ]
            self.assertTrue(include_untracked)
            return [
                FileChange("src/Unstaged.ts", 1, 0),
                FileChange("README.md", 1, 0),
            ]

        with patch("cr.ui.browser.git.changed_files", side_effect=changed_files):
            with patch(
                "cr.ui.browser.git.recent_commits",
                return_value=[
                    CommitSummary(
                        commit="abcdef1234567890",
                        parent=None,
                        authored_at="2026-06-24",
                        subject="Example",
                    )
                ],
            ):
                counts = browser_module._load_scope_home_counts(args)

        self.assertEqual(
            counts,
            {"worktree": 1, "staged": 1, "all": 2, "commits": 1},
        )

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
