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


class ReviewWorkspaceSeenFilterTests(unittest.TestCase):

    def test_browser_remaining_only_filters_seen_paths(self):
        # Behavior: 当用户在workspace中过滤工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/Third.ts", 3, 0),
            ],
            seen_paths={"src/First.ts", "src/Third.ts"},
            remaining_only=True,
        )

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts"],
        )
    def test_review_workspace_marks_selected_file_seen(self):
        # Behavior: 当用户在workspace中选择工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
        )

        self.assertTrue(workspace.mark_selected_seen())
        self.assertEqual(workspace.seen_paths, {"src/Second.ts"})

        self.assertTrue(workspace.unmark_selected_seen())
        self.assertEqual(workspace.seen_paths, set())
    def test_review_workspace_mark_seen_and_advance_uses_remaining_index(self):
        # Behavior: 当用户在workspace中验证工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/Third.ts", 3, 0),
            ],
            selected=0,
            remaining_only=True,
        )

        result = workspace.mark_selected_seen_and_advance()

        self.assertEqual(result.marked_path, "src/First.ts")
        self.assertEqual(result.target_path, "src/Second.ts")
        self.assertTrue(result.had_next_before)
        self.assertEqual(workspace.seen_paths, {"src/First.ts"})
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/Second.ts", "src/Third.ts"],
        )
    def test_review_workspace_mark_seen_and_advance_reports_last_file(self):
        # Behavior: 当用户在workspace遇到工作区时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
        )

        result = workspace.mark_selected_seen_and_advance()

        self.assertEqual(result.marked_path, "src/Second.ts")
        self.assertEqual(result.target_path, "src/Second.ts")
        self.assertFalse(result.had_next_before)
        self.assertEqual(workspace.selected, 1)
        self.assertEqual(workspace.seen_paths, {"src/Second.ts"})

if __name__ == "__main__":
    unittest.main()
