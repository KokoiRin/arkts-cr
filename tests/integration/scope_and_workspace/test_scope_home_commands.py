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


class ScopeHomeCommandTests(unittest.TestCase):

    def test_scope_home_command_opens_scope_home(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「Scope Home 命令 打开 Scope Home」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中执行操作「Scope Home 命令 loads 范围 counts」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中执行操作「Scope Home 刷新 reloads 范围 counts」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「Scope Home count loader counts review 范围 candidates」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
