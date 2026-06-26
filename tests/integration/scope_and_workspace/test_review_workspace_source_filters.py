from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui.browser import (
    BrowserPage,
    BrowserState,
    ReviewScope,
    ReviewWorkspace,
    TaskState,
    _switch_review_scope,
)
from cr.vcs.git import CommitSummary, FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class ReviewWorkspaceSourceFilterTests(unittest.TestCase):

    def test_review_workspace_source_filter_combines_with_path_and_remaining_filters(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「ReviewWorkspace 源码 过滤 combines with 路径 and 剩余 过滤」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0, source="staged"),
                FileChange("src/Second.ts", 2, 1, source="unstaged"),
                FileChange("docs/Third.md", 1, 0, source="staged"),
            ],
            filter_text="src",
            source_filter="staged",
            seen_paths={"src/First.ts"},
            remaining_only=True,
        )

        self.assertEqual(workspace.visible_changes, [])
        workspace.remaining_only = False
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/First.ts"],
        )
    def test_browser_state_syncs_source_filter_with_workspace(self):
        # Behavior: 当用户在Review Scope 与工作区中过滤「browser 状态 syncs 源码 过滤 with workspace」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0, source="staged"),
                FileChange("src/Second.ts", 1, 0, source="unstaged"),
            ],
            source_filter="staged",
        )

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/First.ts"],
        )

        state.source_filter = "unstaged"
        state._sync_to_workspace()
        state._sync_from_workspace()

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts"],
        )
    def test_review_workspace_scope_switch_clears_source_filter(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「ReviewWorkspace 范围 切换 clears 源码 过滤」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        args = argparse_namespace(
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        workspace = ReviewWorkspace(
            [FileChange("src/Old.ts", 1, 0, source="staged")],
            source_filter="staged",
        )

        workspace.switch_scope(
            args,
            ReviewScope(False, False, None, None, False),
            loader=lambda _args: [FileChange("src/New.ts", 1, 0, source="unstaged")],
        )

        self.assertEqual(workspace.source_filter, "")

if __name__ == "__main__":
    unittest.main()
