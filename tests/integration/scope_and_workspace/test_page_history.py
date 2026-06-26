import unittest
from unittest.mock import patch

from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    ReviewScope,
    _switch_review_scope,
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


class PageHistoryTests(unittest.TestCase):

    def test_switch_review_scope_resets_page_history(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「切换 review 范围 重置 页面历史」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
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
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        self.assertTrue(state.page_forward_stack)

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 1, 1)]):
            _switch_review_scope(
                state,
                args,
                ReviewScope(True, False, None, None, False),
            )

        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])

    def test_refresh_resets_page_history_for_reloaded_changes(self):
        # Behavior: 当用户在Review Scope 与工作区中恢复状态「刷新 重置 页面历史 for reloaded changes」时，系统应保存、恢复或重置预期状态 [Requirement: TODO]
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
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        self.assertTrue(state.page_forward_stack)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 1, 1)]):
            with patch("cr.ui.browser._show_commits_when_empty"):
                result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])
