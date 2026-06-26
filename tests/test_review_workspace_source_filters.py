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
